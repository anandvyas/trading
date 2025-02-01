import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from datetime import date, time, timedelta
from abc import ABCMeta, abstractmethod

class BrokerInterface(metaclass = ABCMeta):

    @abstractmethod
    def quote(self, symbol):
        pass

# import all brokers classes
from modules.brokers.breeze import Breeze
from modules.brokers.fyers import Fyers
from modules.brokers.upstox import Upstox
from modules.brokers.dhanhq import Dhan

from modules.utility import Utility
from modules.nse import NSE

u = Utility()
nse = NSE()

class Broker():

    def __init__(self) -> None:

        self.dataProvider = str(u._get("activeDataApiProvider")).title()
        self.activeBroker = str(u._get("activeBroker")).title()

        self.dp = eval(self.dataProvider)()
        self.broker = eval(self.activeBroker)()

    def _getActiveBroker(self):
        return self.broker
    
    def _getDataProvider(self):
        return self.dp

    def _getBrokers(self, broker = None):
        try:
            with open('./configs/brokers.json', 'r+') as f:
                brokerList = json.load(f)
                if broker == None:
                    return brokerList
                else:
                    # check the broker is valid 
                    if broker not in brokerList.keys():
                        logging.error(f"Requested broker not found")
                        return None
                    else:
                        return brokerList[broker]
        except Exception as e:
            logging.error(f"Brokers file not found")
            return None

    def _getATMStrikePrice(self, ltp, round = 100):
        a = (ltp // round) * round
        b = a + round
        return int(b if ltp - a > b - ltp else a)
    
    def _getStrikes(self, atm, strikdiff, count = 15):
        start = atm - (strikdiff * count)
        end = atm + (strikdiff * count) + strikdiff
        return list(range(start, end, strikdiff))

    def _getExpiries(self, symbol:str):
        try:
            df = self._getNFOData(symbol.upper())
            expiries = df["expiry"].unique()
            return expiries.tolist()
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
    
    def _getNFOData(self, symbol:str) -> pd.DataFrame:
        today = datetime.today().date()
        filepath = self.u._createPath(f"{self.name}/NFO-{today}.csv")

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
        return df
    
    def _getAllSymbols(self):
        try:
            df = pd.read_csv('./configs/symbols.csv')
            return df["SYMBOLS"].to_list()
        except Exception as e:
            logging.error(f"Indices/Equity file not found")
            return None

    def _getIndices(self):
        try:
            df = pd.read_csv('./configs/symbols.csv')
            rs = df[(df["TYPE"] == "Index")]
            return rs["SYMBOLS"].to_list()
        except Exception as e:
            logging.error(f"Indices file not found")
            return None
        
    def _getEquities(self):
        try:
            df = pd.read_csv('./configs/symbols.csv')
            rs = df[(df["TYPE"] == "Equity")]
            return rs["SYMBOLS"].to_list()
        except Exception as e:
            logging.error(f"Symbols file not found")
            return None
        
    def _getBrokerSymbol(self, symbol):
        try:
            df = pd.read_csv('./configs/symbols.csv')
            rs = df[(df["SYMBOLS"] == symbol)].reset_index()
            return rs.to_dict(orient='records')[0]
        except Exception as e:
            logging.error(f"Symbols file not found")
            return None
        
    def _getHolidays(self):
        try:
            with open('./configs/holidays.json', 'r+') as f:
                holidays =  json.load(f)
                return holidays["FO"]
        except Exception as e:
            # if holidays file not available we need to read from NSE websites
            # https://www.nseindia.com/api/holiday-master?type=trading - this one will implement later
            logging.error(f"Holidays file not found")
            return None
        
    def _isMarketActive(self):

        marketStartTime = time(9, 15, 0)
        marketEndTime = time(15, 30, 0)
        today = datetime.now()      
        currentTime = today.time()
        currentDate = today.strftime('%Y-%m-%d')

        if currentTime >= marketStartTime or currentTime <= marketEndTime:
            
            # check weekend days
            sun = pd.date_range(start=str(today.year), end=str(today.year+1), 
                    freq='W-SUN').strftime('%Y-%m-%d').tolist()
            sat = pd.date_range(start=str(today.year), end=str(today.year+1), 
                        freq='W-SAT').strftime('%Y-%m-%d').tolist()
            
            if currentDate not in sat and currentDate not in sun :

                marketStatus = nse._getStatus()
                return marketStatus["marketState"][0]["marketStatus"]

        return False

    def qoute(self, symbol):
        print("Hi anand calling this fucntion")
        self.broker.quote()
        pass


