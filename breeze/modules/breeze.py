import os
import json
import urllib
import logging
import pandas as pd
import numpy as np
import time
import datetime
from datetime import date, timedelta
from breeze_connect import BreezeConnect

from modules.utility import Utility
from modules.database import Database

logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

api_key = "8757j163k4V016`99)3g01$IOn#698G0"
secret_key = "9316Y430142BT95lV8122385%tS124R4"
breeze = BreezeConnect(api_key=api_key)

print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus(api_key))
session_token = "23268083"
# breeze.generate_session(api_secret=secret_key,session_token=session_token)

class Breeze():

    # constructor
    def __init__(self) -> None:
        self.u = Utility()
        self.d = Database()
        self.marketStartTime = datetime.time(9, 15, 0)
        self.marketCloseTime = datetime.time(15, 29, 0)

        # login to ICICI Brezee
        url = "https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus(api_key)
        pass

    def _getOptionChain(self, symbol, entryDateTime, expiryDateTime, iteration):

        entryDateTime = datetime.datetime.strptime(f"{entryDateTime}","%Y-%m-%d %H:%M:%S").date()
        expiryDateTime = datetime.datetime.strptime(f"{expiryDateTime}","%Y-%m-%d %H:%M:%S").date()
        
        filepath = self.u._createPath(f"cached/{symbol.upper()}-{expiryDateTime}-{entryDateTime}.json")
        if not os.path.isfile(filepath):
                logging.info(f"File not found {filepath}")

                dataSet = {}
                dates = {}
                strikes = []
                # Create empty structure
                for i, index in enumerate(iteration):
                    ltp = iteration[index]
                    dt = datetime.datetime.strptime(f"{index}","%Y-%m-%d %H:%M:%S")
                    strikes = list(np.unique(strikes + self.u._getStrikePrice(ltp, 100, 10)))
                    dataSet[index] = {}
                    dates[dt.strftime("%Y-%m-%d")] = strikes # need to think here
                    for s in strikes:
                        dataSet[index][str(s)] = {
                            "Call": { "ltp": 0, "open_interest": 0, "volume": 0 },
                            "Put": { "ltp": 0, "open_interest": 0, "volume": 0 },
                        }

                # Download data from API and fill in empty structure
                for i, index in enumerate(dates):
                    for strike in  dates[index]:
                        od = self._getOptionData(symbol, index, expiryDateTime, strike)
                        for df_index, row in od.iterrows():
                            try:
                                dataSet[row["datetime"]][str(int(row["strike_price"]))][row["right"]] = {
                                    "ltp": row["close"],
                                    "open_interest": row["open_interest"], 
                                    "volume": row["volume"]
                                }
                            except Exception as e:
                                print(e)

                # Save dataset in file location
                with open(filepath, 'w') as f:
                    json.dump(dataSet, f)
                    return dataSet
        else:
            logging.info(f"File found {filepath}")
            with open(filepath, 'r') as f:
                return json.load(f)

    def _getOptionData(self, index, date="2021-01-08", expiryDate="2021-01-14", strikePrice = "31900"):
        try:
            logging.info(f"Got request for option:{index}, datetime:{date}, expiry: {expiryDate} strike: {strikePrice}")
            filepathCall = self.u._createPath(f"{index.upper()}/option/{expiryDate}/{date}/{strikePrice}/call.csv")
            filepathPut = self.u._createPath(f"{index.upper()}/option/{expiryDate}/{date}/{strikePrice}/put.csv")
            
            st = datetime.datetime.strptime(f"{date} {self.marketStartTime}","%Y-%m-%d %H:%M:%S")
            et = datetime.datetime.strptime(f"{date} {self.marketCloseTime}","%Y-%m-%d %H:%M:%S")

            if not os.path.isfile(filepathCall):
                logging.info(f"File {filepathCall} not found - fetching from API")
                dataSet = breeze.get_historical_data_v2(interval="1minute",
                                from_date= st.isoformat()[:19] + '.000Z',
                                to_date= et.isoformat()[:19] + '.000Z',
                                stock_code=index.upper(),
                                exchange_code="NFO",
                                product_type="options",
                                expiry_date=f"{expiryDate}T07:00:00.000Z",
                                right="call",
                                strike_price=str(strikePrice))
                
                if dataSet["Error"] == None:
                    df = pd.DataFrame(dataSet["Success"])
                    df.to_csv(filepathCall)
                    time.sleep(1)

            if not os.path.isfile(filepathPut):
                logging.info(f"File {filepathPut} not found - fetching from API")
                dataSet = breeze.get_historical_data_v2(interval="1minute",
                                from_date= st.isoformat()[:19] + '.000Z',
                                to_date= et.isoformat()[:19] + '.000Z',
                                stock_code=index.upper(),
                                exchange_code="NFO",
                                product_type="options",
                                expiry_date=f"{expiryDate}T07:00:00.000Z",
                                right="put",
                                strike_price=str(strikePrice))
                
                if dataSet["Error"] == None:
                    df = pd.DataFrame(dataSet["Success"])
                    df.to_csv(filepathPut)
                    time.sleep(1)

            
            df_call = pd.read_csv(filepathCall)
            df_put = pd.read_csv(filepathPut)
            return pd.concat([df_call, df_put])
        except Exception as e:
            print(e)
    
    def _getStockLTP(self, stock, entryDateTime=datetime.datetime, exitDateTime=datetime.datetime):
        dataSet = {}
        exitDateTime = datetime.datetime.strptime(f"{exitDateTime}","%Y-%m-%d %H:%M:%S")
        delta = timedelta(days=1)
        while entryDateTime <= exitDateTime:
            df = self._getStockData(stock, entryDateTime.date())
            for ind in df.index:
                dataSet[df['datetime'][ind]] = df['close'][ind]
            entryDateTime += delta
        
        return dataSet

    def _getStockData(self, stock, date="2021-01-07"):
        try:
            filepath = self.u._createPath(f"{stock.upper()}/{date}.csv")
            st = datetime.datetime.strptime(f"{date} {self.marketStartTime}","%Y-%m-%d %H:%M:%S")
            et = datetime.datetime.strptime(f"{date} {self.marketCloseTime}","%Y-%m-%d %H:%M:%S")
            
            if not os.path.isfile(filepath):
                logging.info(f"File not found {filepath} - fetching from API")
                dataSet = breeze.get_historical_data_v2(interval="1minute",
                        from_date= st.isoformat()[:19] + '.000Z',
                        to_date= et.isoformat()[:19] + '.000Z',
                        stock_code=stock.upper(),
                        exchange_code="NSE",
                        product_type="cash")
                
                if dataSet["Error"] == None:
                    df = pd.DataFrame(dataSet["Success"])
                    df.to_csv(filepath)
                    time.sleep(1)

                    # Save to database
                    self.d._saveStockData(stock.upper(), df)

            return pd.read_csv(filepath)
        except Exception as e:
            print(e)