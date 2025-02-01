import os
import json
import time
import datetime
from datetime import date, timedelta
from tabulate import tabulate

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
            print(e)
            return False
    
    def _getATMStrikePrice(self, ltp, round = 100):
        a = (ltp // round) * round
        b = a + round
        return int(b if ltp - a > b - ltp else a)
    
    def _getStrikePrice(self, ltp, strikdiff, count = 15):
        ltp = self._getATMStrikePrice(ltp, strikdiff)
        start = ltp - (strikdiff * count)
        end = ltp + (strikdiff * count) + strikdiff
        # print(f"start - {start} end - {end}")
        return list(range(start, end, strikdiff))
    
    def _getExpiry(self, symbol, expiry=["current","next","far"], curDate=datetime.datetime):
        if expiry == "current":
            expiry = self._getCurrentExpiry(symbol,curDate)
        elif expiry == "next":
            expiry = self._getNextExpiry(symbol,curDate)
        elif expiry == "far":
            expiry = self._getFarExpiry(symbol,curDate)
        elif expiry == "month":
            expiry = self._getMonthExpiry(symbol,curDate)
        
        return expiry
    
    def _getLotSize(self, symbol):
        try:
            with open('./files/info.json') as f:
                data = json.load(f)

                # load index expries
                tmp = data["lots"][symbol.upper()]
                return tmp
        except Exception as e:
            print(e)

    def _getStrikeDiff(self, symbol):
        try:
            with open('./files/info.json') as f:
                data = json.load(f)

                # load index expries
                tmp = data["strikdiff"][symbol.upper()]
                return tmp
        except Exception as e:
            print(e)
    
    def _getAllExpiries(self, index=str):
        try:
            with open('./files/info.json') as f:
                data = json.load(f)

                # load index expries
                tmp = data["expiries"][index]
                eDates = tmp.split(",")
                eDates.sort(key=lambda x: time.mktime(time.strptime(x,"%d%b%Y")))
                return list(map(lambda n: datetime.datetime.strptime(f"{n}","%d%b%Y").date(), eDates))
        except Exception as e:
            print(e)

    def _getCurrentExpiry(self, index=str, curDate=datetime.datetime):
        expiries = self._getAllExpiries(index)
        if not isinstance(curDate, datetime.datetime):
            curDate = datetime.datetime.strptime(f"{curDate}","%Y-%m-%d")

        for i in expiries:
            if i > curDate:
                return i.date()

    def _getNextExpiry(self, index=str, curDate=datetime.datetime):
        expiries = self._getAllExpiries(index)
        if not isinstance(curDate, datetime.datetime):
            curDate = datetime.datetime.strptime(f"{curDate}","%Y-%m-%d")

        for i in range(len(expiries)):
            if expiries[i] > curDate:
                return expiries[i + 1].date()

    def _getFarExpiry(self, index=str, curDate=datetime.datetime):
        expiries = self._getAllExpiries(index)
        if not isinstance(curDate, datetime.datetime):
            curDate = datetime.datetime.strptime(f"{curDate}","%Y-%m-%d")

        for i in range(len(expiries)):
            if expiries[i] > curDate:
                return expiries[i + 2].date()

    def _getMonthExpiry(self, index=str, date=datetime):
        pass

    def _getIteration(self, sDate=datetime.datetime, eDate=datetime.datetime, duration=int, excludeMarketCloseDates = bool):
        if not isinstance(sDate, datetime.datetime):
            sDate = datetime.datetime.strptime(f"{sDate} {self.marketStartTime}","%Y-%m-%d %H:%M:%S")

        if not isinstance(eDate, datetime.datetime):
            eDate = datetime.datetime.strptime(f"{eDate} {self.marketEndTime}","%Y-%m-%d %H:%M:%S")

        sDateWithTime = sDate
        marketOpenDates = self._getMarketOpenDates()
        # filter valid dates
        validDates = []
        delta = timedelta(days=1)
        while sDate <= eDate:
            if excludeMarketCloseDates == True:
                t = datetime.datetime(sDate.year, sDate.month, sDate.day, 0,0)
                if t in marketOpenDates:
                    validDates.append(sDate.date())
            else:
                validDates.append(sDate.date())
            sDate += delta

        validDatesWithTimeRange = []
        delta = timedelta(minutes=duration)
        for d in validDates:
                if d == sDateWithTime.date():
                    st = sDateWithTime
                else:
                    st = datetime.datetime.strptime(f"{d} {self.marketStartTime}","%Y-%m-%d %H:%M:%S")
                
                et = datetime.datetime.strptime(f"{d} {self.marketEndTime}","%Y-%m-%d %H:%M:%S")
                while st <= et:
                    validDatesWithTimeRange.append(st)
                    st += delta
        
        return validDatesWithTimeRange

    def _getMarketOpenDates(self):
        try:
            with open('./files/info.json') as f:
                data = json.load(f)

                # load index valid dates
                tmp = data["dates"]
                return list(map(lambda n: datetime.datetime.strptime(f"{n}","%Y-%m-%d"), tmp))
        except Exception as e:
            print(e)

    def _getOrderKey(self, symbol, date, strike, type):
        date = datetime.datetime.strptime(f"{date}","%Y-%m-%d %H:%M:%S")
        return f"{symbol.upper()}{date.day}{date.month}{strike}{type.upper()}"

    def _output(self, rows = []):
        headers = ["Date","Lots","Type", "Strike", "Expiry", "Entry","LTP", "P/L"]
        return tabulate(rows, headers, tablefmt = 'pretty')


