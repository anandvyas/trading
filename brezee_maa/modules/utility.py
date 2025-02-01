import os
import json
import time
import logging
import datetime
import pandas as pd
from datetime import date, timedelta
from tabulate import tabulate

logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

class Utility:

    def __init__(self) -> None:
        self.dataFolder = "dataX"
        self.marketStartTime = datetime.time(9, 15, 0)
        self.marketEndTime = datetime.time(15, 30, 0)
        pass

    def _createPath(self, path):
        filepath = f"./{self.dataFolder}/{path}"
        if self._createDir(filepath):
            return filepath

    def _createDir(self, filepath):
        dirname = os.path.dirname(filepath)
        try:
            isExist = os.path.exists(dirname)
            if not isExist:
                os.makedirs(dirname)
                return True
            else:
                return True
        except Exception as e:
            logging.DEBUG(str(e))
            return False
        
    def _getATMStrikePrice(self, ltp, round = 100):
        a = (ltp // round) * round
        b = a + round
        return int(b if ltp - a > b - ltp else a)
    
    def _getStrikes(self, atm, strikdiff, count = 15):
        start = atm - (strikdiff * count)
        end = atm + (strikdiff * count) + strikdiff
        return list(range(start, end, strikdiff))

    def _getLotSize(self, symbol):
        try:
            with open('./data/settings.json') as f:
                data = json.load(f)

                # load index expries
                tmp = data["lots"][symbol.upper()]
                return tmp
        except Exception as e:
            print(e)

    def _getStrikeDiff(self, symbol):
        try:
            with open('./data/settings.json') as f:
                data = json.load(f)

                # load index expries
                tmp = data["strikdiff"][symbol.upper()]
                return tmp
        except Exception as e:
            print(e)

    def _isHoliday(self):
        try:
            with open('./data/settings.json') as f:
                data = json.load(f)

                # load index expries
                today = datetime.datetime.today()

                sun = pd.date_range(start=str(today.year), end=str(today.year+1), 
                         freq='W-SUN').strftime('%m/%d/%Y').tolist()
                sat = pd.date_range(start=str(today.year), end=str(today.year+1), 
                         freq='W-SAT').strftime('%m/%d/%Y').tolist()
                
                df = pd.DataFrame(data["holidays"])
                holidays = pd.to_datetime(df["tradingDate"], utc=True)
                
                if today in sun:
                    logging.info("Sunday - Market closed")
                    return True
                elif today in sat:
                    logging.info("Saturday - Market closed")
                    return True
                elif today in holidays.values:
                    logging.info("National holiday - Market closed")
                    return True
                else:
                    logging.info(f"Today {today.date()} is trading day...")
                    False

        except Exception as e:
            print(e)

    def _isMarketActive(self):
        currentTime = datetime.time()
        if currentTime >= self.marketStartTime and currentTime <= self.marketEndTime:
            return True
        else:
            return False

    def _get(self, key:str):
        try:
            with open('./data/data.json', 'r+') as f:
                data = json.load(f)
                if key in data:
                    return data[key]
        except Exception as e:
            logging.error(f"{e}-{key} - key not found")
            return None


    def _set(self, key, val):
        with open('./data/data.json', 'r+') as f:
            data = json.load(f)
            data[key] = val
            f.seek(0)  
            json.dump(data, f, indent=4)
            f.truncate()
