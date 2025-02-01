import threading
import queue
import logging
import time 
import json
import sys
import asyncio
import pandas as pd
from time import sleep
from datetime import datetime, time, timedelta

# from modules.brezee import Breeze
from modules.fyers import Fyers
from modules.dhan import Dhan
from modules.database import Database as DB
from modules.utility import Utility

logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

class Strategies:

    #initialize strategy object
    def __init__(self,client="Breeze",symbol="NIFTY", strategy="weekly_short_straddle",lots=1, targetedProfit=5, targetedLoss=2, live = False):
        self.u = Utility()
        self.db = DB()
        self.socket = 0
        self.maxloss = int(targetedLoss)
        self.maxprofit = int(targetedProfit)
        self.symbol = symbol.upper()
        self.papertrading = not live
        self.flag = False
        self.lots = lots
        self.orders = pd.DataFrame({})

        # self.api = eval(client.title())()
        self.api = Fyers(self.papertrading)

        getattr(self, str(strategy), lambda: False)()

    # Rules
    # timeframe weekly 
    # Sell ATM and buy OTM () for margin benifit
    # check the breakeven difference should be greater than 200 both side at day end
    # Don't make any entry on expiry day after 12PM
    # Close all the position on expiry day at 3:15PM
    def weekly_short_straddle(self):
        
        isReady = False
        requiredPreminum = 56000
        breakeven_call_ratio = 0
        breakeven_put_ratio = 0
        
        # Create name of the stratagy 
        expiry = self.api._getExpiry(self.symbol,"next")
        StrategyName = f'Weekly-Option-{self.symbol.title()}-{expiry}'

        # Get Underline assest info
        # Get real name of INDEX based on broker
        underlying = self.api._getIndexSymbol(self.symbol)
        underlyingltp = self.api._getLTP(underlying)
        underlyingLotSize = self.u._getLotSize(self.symbol)
        underlyingStrikeDiff = self.u._getStrikeDiff(self.symbol)
        underlyingATM = self.u._getATMStrikePrice(underlyingltp, underlyingStrikeDiff)
        strikes = self.u._getStrikes(underlyingATM, underlyingStrikeDiff, 15 )

        # check all existing orders of this strategy
        self.orders = self.db._getOrders(StrategyName)
        if self.orders.empty:
            atmIndex = strikes.index(underlyingATM)
            bc_strike = strikes[atmIndex + 5]
            bp_strike = strikes[atmIndex - 5]
            sc_strike = strikes[atmIndex]
            sp_strike = strikes[atmIndex]

            buyCall = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, bc_strike,expiry,"call", "B",lots = self.lots)
            buyPut = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, bp_strike,expiry,"put", "B",lots = self.lots)
            sellCall = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, sc_strike, expiry,"call", "S",lots = self.lots)
            sellPut = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, sp_strike, expiry,"put", "S",lots = self.lots)
            
            # print(f"{buyCall}- {buyPut} - {sellCall} - {sellPut}")
            self.orders = self.api._enterPositions(StrategyName, pd.DataFrame([buyCall, buyPut, sellCall, sellPut]))
            self.db._saveOrders(StrategyName, self.orders)
            
            # check failed orders
            if "failed" in self.orders["status"].to_list():
                print("failed in execution...., revert back")
            
        # calculate breakeven
        debit = self.orders.loc[self.orders["side"] == "B", "ltp"].sum()
        credit = self.orders.loc[self.orders["side"] == "S", "ltp"].sum()
        totCredits = credit - debit

        callStrike = self.orders.loc[(self.orders["right"] == "CE") & (self.orders["side"] == "S"),"strike"].item()
        putStrike = self.orders.loc[(self.orders["right"] == "PE") & (self.orders["side"] == "S"),"strike"].item()
        
        breakeven_up = callStrike + totCredits
        breakeven_down = putStrike - totCredits
        logging.info(f' Call strike - {callStrike} BE-UP - {breakeven_up}  BE-DOWN - {breakeven_down} ')
        
        # start socket and register all the symbols which is in stra
        data_ws = None
        def ws_on_open():
            logging.info(f"Websocket open successfully")
            # subscribe underlying and others symbols
            data_ws.subscribe([underlying])
            data_ws.subscribe(self.orders["symbol"])
            data_ws.keep_running()

        def ws_on_close(message):
            logging.info(f"Websocket close successfully: {message}")

        def ws_on_error(message):
            logging.error(f"Websocket: {message} ")

        def ws_on_message(message):

            if message["symbol"] == underlying:
                action_alert = 60
                ltp = message["ltp"]
                breakeven_call_ratio = abs(((breakeven_up - ltp) * 100) / totCredits)
                breakeven_put_ratio = abs(((breakeven_down - ltp) * 100) / totCredits)

                if breakeven_call_ratio < action_alert:
                    print(f"Call side adjustment required...")
                    callOrders = self.orders.loc[self.orders["right"] == "CE"]
                    self.orders = pd.concat([self.orders, self.api._exitPositions(StrategyName, callOrders)]).drop_duplicates(['symbol','strike'],keep='last').sort_index()

                    # Make new position
                    underlyingATM = self.u._getATMStrikePrice(underlyingltp, underlyingStrikeDiff)
                    atmIndex = strikes.index(underlyingATM)
                    bc_strike = strikes[atmIndex + 7]
                    sc_strike = strikes[atmIndex + 5]
                    
                    buyCall = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, bc_strike,expiry,"call", "B",lots = self.lots)
                    sellCall = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, sc_strike, expiry,"call", "S",lots = self.lots)

                    o = self.api._enterPositions(StrategyName, pd.DataFrame([buyCall, sellCall]))
                    self.orders = pd.concat([self.orders, o]).reset_index(drop=True)
                    self.db._saveOrders(StrategyName, self.orders)

                elif breakeven_put_ratio < action_alert:
                    print(f"Put side adjustment required...")
                    putOrders = self.orders.loc[self.orders["right"] == "PE"]
                    self.orders = pd.concat([self.orders, self.api._exitPositions(StrategyName, putOrders)]).drop_duplicates(['symbol','strike'],keep='last').sort_index()

                    # Make new position
                    underlyingATM = self.u._getATMStrikePrice(underlyingltp, underlyingStrikeDiff)
                    atmIndex = strikes.index(underlyingATM)
                    bp_strike = strikes[atmIndex - 7]
                    sp_strike = strikes[atmIndex - 5]
                    
                    buyPut = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, bp_strike,expiry,"put", "B",lots = self.lots)
                    sellPut = self.api._getOrderStruct(self.symbol, underlyingltp, underlyingLotSize, sp_strike, expiry,"put", "S",lots = self.lots)

                    o = self.api._enterPositions(StrategyName, pd.DataFrame([buyPut, sellPut]))
                    self.orders = pd.concat([self.orders, o]).reset_index(drop=True)
                    self.db._saveOrders(StrategyName, self.orders)

            else:
                if message["ltp"] > 0:
                    self.orders.loc[(self.orders["symbol"] == message["symbol"]) & (self.orders["status"] == "traded"), "cltp"] = message["ltp"]
                    qltp = self.orders["qty"] * self.orders["ltp"]
                    qcltp = self.orders["qty"] * self.orders["cltp"]
                    self.orders.loc[self.orders['side'] == 'B', 'pl'] =  qcltp - qltp
                    self.orders.loc[self.orders['side'] == 'S', 'pl'] =  qltp - qcltp
            
            
            print(self.orders)
            totPre = requiredPreminum * self.lots
            pl = self.orders["pl"].sum()
            per = round((pl * 100) / totPre , 2)
            print(f'Invested: {totPre} PL: {pl} precentage: {per}% BC R - {breakeven_call_ratio} BP R - {breakeven_put_ratio}' )

        if(self.socket == 0):
            logging.info(f"Websocket closed: try to open...")
            data_ws = self.api.ws_connect()
            data_ws.on_open = ws_on_open
            data_ws.On_error = ws_on_error
            data_ws.on_close = ws_on_close
            data_ws.On_message = ws_on_message
            data_ws.connect()
            self.socket = 1