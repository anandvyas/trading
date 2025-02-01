import os
import logging
import threading
import queue
import random
from urllib.parse import parse_qs, urlparse
import base64
import requests
import pandas as pd
import duckdb as db
from time import time, sleep
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from pyotp import TOTP

from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws, order_ws

from modules.utility import Utility
from modules.database import Database as DB

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

client_id = os.environ.get("FYERS_CLIENT_ID") 
fy_id = os.environ.get("FYERS_ID") 
redirect_uri = os.environ.get("FYERS_REDIRECT_URI")
secret_key=os.environ.get("FYERS_SECRET_KEY")
totp=os.environ.get("FYERS_TOTP")
pin=os.environ.get("FYERS_PIN")

index_symbols = {
    "MIDCPNIFTY": "NSE:MIDCPNIFTY-INDEX",
    "FINNIFTY": "NSE:FINNIFTY-INDEX",
    "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
    "NIFTY": "  "
}

class Fyers():

    def __init__(self, papertrading = False) -> None:
        self.u = Utility()
        self.db = DB()
        self.broker = "fyers"
        self.symbols = pd.DataFrame()
        self.papertrading = papertrading

        # validate the token
        self.accessToken = self.u._get(f"{self.broker}_access_code")
        self.fyers = fyersModel.FyersModel(client_id = client_id, is_async=False,
                                      token=self.accessToken, log_path="./logs/fyers")
        
        profile = self.fyers.get_profile()
        if profile["s"] == "error":
            logging.debug(f'Fyers - {profile["message"]}')
            logging.debug(f'Fyers - Initiate the login process')
            self.fyers = self._login()
            profile = self.fyers.get_profile()
        
        logging.debug(f'Fyers - access token validated, welcome {profile["data"]["name"]}')

    def _getIndexSymbol(self, index):
        if index in ["MIDCPNIFTY","FINNIFTY","BANKNIFTY","NIFTY"]:
            return index_symbols[index]
        else:
            return False
        
    def _getOrderbook(self):
        ob = self.fyers.orderbook()
        print(ob)

    def _getExpiries(self, symbol:str):
        try:
            df = self._getNFOData(symbol.upper())
            return df["expiry"].unique()
        except Exception as e:
            logging.error(str(e))

    def _getCurrentExpiry(self, symbol:str):
        return self._getExpiries(symbol.upper())[0]
    
    def _getNextExpiry(self, symbol:str):
        return self._getExpiries(symbol.upper())[1]
    
    def _getFarExpiry(self, symbol:str):
        return self._getExpiries(symbol.upper())[2]
    
    def _getExpiry(self, symbol:str, expiry = "next"):
        if expiry not in ["current","next","far"]:
            expiry = "next"
        
        return eval(f"self._get{expiry.title()}Expiry")(symbol.upper())

    def _getOrderStruct(self, underlying, underlyingltp, underlyingLotSize, strike, expiry:datetime, right:str, side = ["b","s"], lots = 1):
        right = right.lower()
        strike = float(strike)
        right = 'CE' if right.lower() == 'call' else 'PE'
        qty = underlyingLotSize * lots
        symbol = self._getSymbol(underlying, strike, expiry, right)
        ltp = self._getLTP(symbol)

        data = {
            "symbol":symbol,
            "strike": strike,
            "expiry": expiry.strftime("%d-%m-%Y"),
            "right": right,
            "qty":qty,
            "status": "pending",
            "ltp": ltp,
            "cltp": ltp,
            "initiated_time": datetime.now().strftime("%H:%M:%S"),
            "executed_time": "",
            "underlying": underlying,
            "underlyingltp": underlyingltp, # underlying LTP
            "side":side.upper(),
        }
        return data

    def _getSymbol(self, underlying, strike, expiry, right:str):
        try:
            strike = float(strike)
            df = self._getNFOData(underlying.upper())
            df = df[(df["expiry"] == expiry) & (df["right"] == right) & (df["strike"] == strike)]
            return df["symbol"].values[0]
        except Exception as e:
            logging.error(str(e))

    def _getNFOData(self, symbol:str) -> pd.DataFrame:
        today = datetime.today().date()
        filepath = self.u._createPath(f"{self.broker}/NFO-{today}.csv")
        if self.symbols.empty:
            logging.debug(f"fetching symbol list from file")
            if not os.path.isfile(filepath):
                url = "https://public.fyers.in/sym_details/NSE_FO.csv"
                logging.info(f"File not found {filepath}, downloading file {url} ...")

                r = requests.get(url, allow_redirects=True)
                open(filepath, 'wb').write(r.content)

            headers = ["symbol_long_id","symbol_big","NA1","NA2","NA3","NA4","market_start_end_time","previous_day","expiry","symbol","NA5","NA6","symbol_short_id","underlying","underlying_short_id","strike","right","underlying_long_id","NA7"]
            df =  pd.read_csv(filepath, names=headers)
            df = df[df["underlying"] == symbol.upper()]
            df["expiry"] = pd.to_datetime(df["expiry"], unit="s").dt.date
            self.symbols = df[["expiry","symbol","underlying","strike","right"]]
        
        return self.symbols

    def _isMarketActive(self):
        # Exchange : 10-NSE 12-BSE
        # Segments : 10-Capital Market 11-Equity Derivatives 12-Currency Derivatives 20-Commodity Derivatives
        rs = self.fyers.market_status()
        if rs["code"] == 200:
            df = pd.DataFrame(rs["marketStatus"])
            status = df.loc[(df["exchange"] == 10) & (df["segment"] == 11)]["status"].values.item()
            if status == "OPEN":
                return True
            else:
                logging.info(f"Today is holiday, enjoy you day !!!")
                return False
    
    def _getLTP(self, stock_code:str) -> float:
        try:
            data = { "symbols": stock_code }
            return float(self.fyers.quotes(data)['d'][0]['v']['lp'])
        except Exception as e:
            logging.error(str(e))   

    def _orderPlace(self, order):
        side = 1 if order["side"] == "B" else -1
        data = {
            "symbol":order["symbol"],
            "qty":order["qty"],
            "type":2,
            "side":side,
            "productType":"MARGIN",
            "limitPrice":0,
            "stopPrice":0,
            "validity":"DAY",
            "disclosedQty":0,
            "offlineOrder":False,
        }
        logging.info(f'Order initiating - {order["symbol"]} - {order["qty"]} - {order["side"]}')
        
        if not self.papertrading:
            response = self.fyers.place_order(data=data)
        else:
            order_id = random.randint(100000000000,999999999999)
            response =  {
                "s": "ok",
                "code": 1101,
                "message": f"Order submitted successfully. Your Order Ref. No.{order_id}",
                "id": order_id
            }

        if response["s"] == "ok":
            logging.info(response["message"])
            return response
        else:
            logging.error(response["message"])
            return response

    def _orderExit(self, symbol_id):
        data = { "id": symbol_id }
        print(data)
        if not self.papertrading:
            response = self.fyers.exit_positions(data=data)
        else:
            response =  {
                "s": "ok",
                "code": 200,
                "message": f"The position is closed."
            }

        if response["s"] == "ok":
            logging.info(response["message"])
            return response
        else:
            logging.error(response["message"])
            return response

    # Bulk exit positions - close all sell position first and then buy position 
    def _exitPositions(self, StrategyName, orders:pd.DataFrame):
        # close all sell orders first
        sellOrder = orders.loc[orders["side"] == "S"]
        for index, row in sellOrder.iterrows():
            response = self._orderExit(row["symbol"])
            if response["s"] == "ok":
                # update record in DF
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "exited"
            else:
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "failed"

        buyOrder = orders.loc[orders["side"] == "B"]
        for index, row in buyOrder.iterrows():
            response = self._orderExit(row["symbol"])
            if response["s"] == "ok":
                # update record in DF
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "exited"
            else:
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "failed"

        return orders
            
    # Bulk enter positions - execute all buy position first and then sell positions
    def _enterPositions(self, StrategyName, orders:pd.DataFrame):

        # execute all buy orders to take margin 
        buyOrder = orders.loc[orders["side"] == "B"]
        for index, row in buyOrder.iterrows():
            orders.loc[orders["symbol"] == row["symbol"], "executed_time"] = datetime.now().strftime("%H:%M:%S")
            response = self._orderPlace(row.to_dict())
            if response["s"] == "ok":
                # update record in DF
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "traded"
            else:
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "failed"

        # execute all buy orders to take margin 
        sellOrder = orders.loc[orders["side"] == "S"]
        for index, row in sellOrder.iterrows():
            orders.loc[orders["symbol"] == row["symbol"], "executed_time"] = datetime.now().strftime("%H:%M:%S")
            response = self._orderPlace(row.to_dict())
            if response["s"] == "ok":
                # update record in DF
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "traded"
            else:
                orders.loc[orders["symbol"] == row["symbol"], "status"] = "failed"

        return orders

    def ws_connect(self):
        return data_ws.FyersDataSocket(
            access_token=self.accessToken,       # Access token in the format "appid:accesstoken"
            log_path="./logs/fyers",                     # Path to save logs. Leave empty to auto-create logs in the current directory.
            litemode=False,                  # Lite mode disabled. Set to True if you want a lite response.
            write_to_file=False,              # Save response in a log file instead of printing it.
            reconnect=True
        )

    def _getEncodedString(self, string):
        string = str(string)
        base64_bytes = base64.b64encode(string.encode("ascii"))
        return base64_bytes.decode("ascii")

    def _login(self):

        logging.debug(f"Fyers - token expired, initiating login process")
        logging.debug(f"Fyers - entering first login process")
        # First step of login
        url = f"https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
        payload = {
            "fy_id": self._getEncodedString(fy_id), 
            "app_id": "2"
        }
        res = requests.post(url=url, json=payload).json()
        
        # Second level of auth - send TOTP
        logging.debug(f"Fyers - entering second login process - TOTP verification")
        url = f"https://api-t2.fyers.in/vagator/v2/verify_otp"
        payload = {
            "request_key": res["request_key"], 
            "otp":TOTP(totp).now()
        }
        res = requests.post(url=url, json=payload).json()
        sleep(1)

        # Third level of auth - send PIN
        # Step 3 - Verify pin and send back access token
        logging.debug(f"Fyers - entering third login process - PIN verification")
        ses = requests.Session()
        url = f"https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
        payload = {
            "request_key": res["request_key"],
            "identity_type":"pin",
            "identifier":self._getEncodedString(pin)
        }
        res = ses.post(url=url, json=payload).json()
        sleep(1)
        
        ses.headers.update({
            'authorization': f"Bearer {res['data']['access_token']}"
        })
        
        payload = {
            "fyers_id": fy_id, 
            "app_id": client_id[:-4], 
            "redirect_uri": redirect_uri, 
            "appType": "100",
            "code_challenge": "", "state": "None", "scope": "", "nonce": "", "response_type": "code", "create_cookie": True
        }
        
        logging.debug(f"Fyers - entering fourth login process - get Access Token")
        authres = ses.post('https://api.fyers.in/api/v2/token', json=payload).json()
        parsed = urlparse(authres["Url"])
        auth_code = parse_qs(parsed.query)['auth_code'][0]
        
        appSession = fyersModel.SessionModel(client_id = client_id,
                                             secret_key= secret_key,
                                             redirect_uri = redirect_uri,
                                             response_type='code',
                                             grant_type='authorization_code')
        
        appSession.set_token(auth_code)
        response = appSession.generate_token()
        access_token = response["access_token"]

        logging.debug(f"Fyers - save Access Token in file")
        self.u._set(f"{self.broker}_access_code",access_token)

        return fyersModel.FyersModel(client_id = client_id, is_async=False,
                                      token=access_token, log_path=os.getcwd())


        