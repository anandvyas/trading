import json
import logging
import requests
import calendar
import datetime as date

class NSE:

    def __init__(self) -> None:
        self.headers = {
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://www.nseindia.com/option-chain?symbol=NIFTY",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36"
        }

    def _getStatus(self):
        url = "https://www.nseindia.com/api/marketStatus"
        res = requests.get(url, headers= self.headers).text
        return json.loads(res)
        
    def _getExpiries(self, limit = None):
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        res = requests.get(url, headers= self.headers).text
        res = json.loads(res)

        returnObj = []
        # Change date in datetime object
        if res["records"]["expiryDates"]:
            for d in res["records"]["expiryDates"]:
                d = date.datetime.strptime(d, "%d-%b-%Y")
                if d > date.datetime.now():
                    time_change = date.timedelta(hours=15, minutes=30)
                    d = d + time_change
                    returnObj.append(d)

        return returnObj[1:limit + 1]

    def _isMonthlyExpiry(self, expiry):
        month = calendar.monthcalendar(expiry.year, expiry.month)
        thrusday = max(month[-1][calendar.THURSDAY], month[-2][calendar.THURSDAY])
        if expiry.day == thrusday:
            return True
        else:
            return False

    def _getOptionSymbols(self, atm, symbol = 'NSE:NIFTYBANK-INDEX'):
        expiries = self._getExpiries(3)
        symbol = symbol.upper()

        stockDict = {
            "NSE:NIFTY50-INDEX": "NIFTY",
            "NSE:BANKNIFTY-INDEX": "BANKNIFTY",
            "NSE:NIFTYBANK-INDEX": "BANKNIFTY",
        }

        name = stockDict[symbol]

        res = {}
        res[symbol] = {}
        for expiry in expiries:
            base = ""
            if self._isMonthlyExpiry(expiry):
                base = f'NSE:{name}{expiry.strftime("%y%-b")}{atm}'.upper()
            else:
                base = f'NSE:{name}{expiry.strftime("%y%-m%d")}{atm}'.upper()

            res[f'{base}CE'] = {"ltp": 0, "base": base, "expiry": expiry, "type": "c"}
            res[f'{base}PE'] = {"ltp": 0, "base": base, "expiry": expiry, "type": "p"}

        return res