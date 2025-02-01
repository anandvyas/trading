import os
import base64
import logging
import requests
import pandas as pd
from urllib.parse import parse_qs, urlparse
from time import time, sleep
from datetime import datetime
from dotenv import load_dotenv
from pyotp import TOTP

from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws, order_ws

from modules.utility import Utility
from .broker import BrokerInterface

load_dotenv()

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
    "NIFTY": "NSE:NIFTY50-INDEX"
}

class Fyers(BrokerInterface):

    def __init__(self, salt='SlTKeYOpHygTYkP3') -> None:
        self.name = "FYERS"
        self.u = Utility()
        self.symbols = pd.DataFrame()

        # validate the token
        self.accessToken = self.u._get(f"{self.name}_access_code")
        self.fyers = fyersModel.FyersModel(client_id = client_id, is_async=False,
                                      token=self.accessToken, log_path="./logs/fyers")
        
        profile = self.fyers.get_profile()
        if profile["s"] == "error":
            logging.debug(f'Fyers - {profile["message"]}')
            logging.debug(f'Fyers - Initiate the login process')
            self.fyers = self._login()
            profile = self.fyers.get_profile()

    def quote(self, stock_code:str):
            stock_code = stock_code.upper()
            query = { "symbols": stock_code }
            rs = self.fyers.quotes(query)
            if rs['d'][0]['s'] == 'error':
                return None
            else:
                 return rs['d'][0]['v']['cmd']['c']
    
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
    
    def historical(self, symbol, resolution, range_from, range_to):

        resolution_dict = {
            "1min": "1",
            "3min": "3",
            "5min": "5",
            "10min": "10",
            "15min": "15",
            "30min": "30",
            "hour": "60",
            "day": "1D"
        }
        
        data = {
            "symbol": symbol,
            "resolution": resolution_dict[resolution],
            "date_format": "1",
            "range_from": range_from,
            "range_to": range_to,
            "cont_flag": "1"
        }

        try:
            rs = self.fyers.history(data=data)
            if rs['s'] == 'error':
                return None
            else:
                 return rs['candles']
        except Exception as e:
            logging.error(e)
            return None
        
        

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
        self.u._set(f"{self.name}_access_code",access_token)

        return fyersModel.FyersModel(client_id = client_id, is_async=False,
                                      token=access_token, log_path=os.getcwd())


        