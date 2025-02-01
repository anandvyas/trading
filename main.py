from time import time, sleep
from datetime import date, datetime, timezone
from os.path import join, dirname
from tkinter import NS
from dotenv import load_dotenv
import logging
import random

from modules.utils import utils 
from modules.fyers import Fyers
from modules.nse import NSE
from modules.greeks import GREEKS
from modules.telegram import TG
from modules.strategies import Strategies

# Trading packages
import pandas as pd

# Config
logging.basicConfig(filename="logs.txt",level=logging.INFO)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

class OptionBot:

    def __init__(self, *args, **kwargs) -> None:
        logging.info("Good Morning !!! ")
        try:
            self.nse = NSE()
            self.greeks = GREEKS()
            self.fyers = Fyers()
            self.tg = TG()

            self.symbol = "NSE:NIFTY50-INDEX"
            self.lot = 50
            
            # Get LTP
            self.ltp = self.fyers._getLtp(self.symbol)
            self.atm = round(self.ltp/self.lot)*self.lot

            # Get Option Symbols
            self.options = self.nse._getOptionSymbols(self.atm, self.symbol)
            optionSymbols = list(self.options.keys())

            # initiate socket
            self.fs = self.fyers._getWSToken()
            self.fs.websocket_data = self._tick
            self.fs.subscribe(optionSymbols, data_type="symbolData")
            self.fs.keep_running()

        except Exception as e:
            logging.error(str(e))


    def _strategy(self, base):
        try:
            call = base + "CE"
            put = base + "PE"
            diff = abs(self.options[call]["iv"] - self.options[put]["iv"])
            if diff < 0.5:
                self.tg._send(f" {call} and {put} difference is less then 0.5 {diff}")

            print(base,"-- c: ",self.options[call]["iv"]," p: ",self.options[put]["iv"], " diff: ", diff)

        except Exception as e:
            # logging.error(str(e))
            print(str(e))

    def _tick(self, data):
        tick = data[0]
        if tick["symbol"] == self.symbol:
            self.ltp = tick["ltp"]

            # checking, is there any change in ATM
            atm = round(self.ltp/self.lot)*self.lot

            # print("ltp: ", tick["ltp"], " ATM: ", atm)

            # if atm != self.atm:
            #     print("change in ATM")
            #     print("change in ATM")
            #     print("change in ATM")
        else:
            t = self.options[tick["symbol"]]
            self.options[tick["symbol"]]["ltp"] = tick["ltp"]
            self.options[tick["symbol"]]["iv"] = self.greeks.iv(tick["ltp"], self.ltp, self.atm, t["expiry"], 0.1, t["type"])
            self._strategy(self.options[tick["symbol"]]["base"])

OptionBot()





# import pandas_ta as ta
# import vectorbt as vbt



# nse = NSE()
# greeks = GREEKS()
# fyers = Fyers()
# tg = TG()



# def option_data(msg):
#     print(f"{msg}")

# ltp = fyers._getLtp("NSE:NIFTYBANK-INDEX")
# # tg._send(f" NIFTYBANK: {ltp} getting ATM option symbols")

# symbols = nse._getOptionSymbols(ltp, 'BANKNIFTY')
# tmp = ','.join(symbols)
# # tg._send(f" NIFTYBANK: {ltp} - {tmp}")

# fs = fyers._getWSToken()
# fs.websocket_data = option_data
# fs.subscribe(symbols)
# fs.keep_running()


# tmp = greeks.iv(470, 38237.40, 38300, datetime(2022,8,18,15,30), 0.1, 'c')
# print(tmp)
# tmp = greeks.iv(481, 38237.40, 38300, datetime(2022,8,18,15,30), 0.1, 'p')
# print(tmp)
# print(symbols)


# expiries = nse._getExpiries(3)

# print(expiries)



# download data 
# utils._fetchData("ICICIBANK", token="AAAAABi5h1Bja8Pwu8R2W6CtBHbQXTO7YtpvUgPDXLzpYhXeJmkxobVRNuUIGNRWV6HjuhT2gqPlv9cgbiuskicN0-0vVJ7Z3HpFxerjepyG_uTfD7T0pk%3D" '1h')

# df = pd.DataFrame()
# df = pd.read_csv("./data/data.csv")

# # start_date = "2020-01-01"
# # end_date   = "2020-12-31"
# # df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

# df["date"] = pd.DatetimeIndex(df.date)
# df = df.set_index("date")

# df['entries_pos'] = Strategies._macdCrossover(df, 7, 21)

# df.dropna(inplace=True)
# df.reset_index(drop=False, inplace=False)

# df = utils._addEntryExit(df, 2, 2)

# pf = vbt.Portfolio.from_signals(df.close, df.entries, df.exits, fees=0, init_cash=10000)
# print(pf.orders.records_readable.to_string())
# print(pf.stats())
