import datetime
from datetime import date, timedelta
import pandas as pd
import pandas_ta as ta
import logging
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(message)s',level=logging.DEBUG)

from modules.breeze import Breeze
from modules.utility import Utility
# from modules.database import Database

class BackTesting():

    def __init__(self, symbol, entryDateTime, exitDateTime, target=5, loss=2, lots=1, strategy = "weekly_short_straddle") -> None:
        self.b = Breeze()
        self.u = Utility()
        # self.d = Database()

        # global variables
        self.count = 0
        self.symbol = symbol.upper()
        self.entryDateTime = entryDateTime.date()
        self.exitDateTime = exitDateTime.date()
        self.lots = lots
        self.lotsize = self.u._getLotSize(self.symbol)
        self.strikeDiff = self.u._getStrikeDiff(self.symbol)
        self.breakeven = {}
        self.premium = 0
        self.target = target
        self.loss = loss
        self.allOrders = {}
        self.orders = {}
        self.curExpiry = ""
        self.curpl = 0 # current profit and loss
        self.maxloss = 0
        self.maxprofit = 0
        self.targetedProfit = 0
        self.targetedLoss = 0

        self.summary = {}

        self.stockLTP = {}
        self.optionChain = {}

        getattr(self, str(strategy), lambda: False)()

    def _order(self, entryDateTime:datetime, expiry:str, strike:str, type:str, lots:int, opr:str):
        if entryDateTime not in self.orders:
            self.orders[entryDateTime] = {}

        if strike not in self.orders[entryDateTime]:
            self.orders[entryDateTime][strike] = {}

        self.count = self.count + 1
        self.orders[entryDateTime][strike][type] = {
            "index": self.count,
            "active": True, 
            "opr": opr.upper(),
            "entryDateTime": str(entryDateTime),
            "lots": lots,
            "type": type.upper(),
            "strike" : strike,    
            "expiry": str(expiry.date()),
            "entryltp": self.optionChain[entryDateTime][strike][type]["ltp"],
            "ltp": self.optionChain[entryDateTime][strike][type]["ltp"],
            "pl": 0
        }
        logging.debug(f"New order created {opr} Expiry: {expiry} EntryTime: {entryDateTime} Strike: {strike} Type: {type}")
        return self.optionChain[entryDateTime][strike][type]["ltp"]
    
    def _orderUpdate(self, curTime:datetime):
        pl = 0 
        credit = 0
        debit = 0
        for time in self.orders:
            for strike in self.orders[time]:
                for type in self.orders[time][strike]:
                    order = self.orders[time][strike][type]

                    # update order ltp
                    if order["active"] == True and self.optionChain[curTime][strike][type]["ltp"] > 0:
                        order["ltp"] = self.optionChain[curTime][strike][type]["ltp"]

                    # calculate Max Profit and Max Loss
                    if order["opr"] == "S":
                        credit = round(credit + order["entryltp"],2)
                        order["pl"] = (order["entryltp"] - order["ltp"]) * (order["lots"] * self.lotsize)
                    elif  order["opr"] == "B":   
                        debit = round(debit + order["entryltp"],2)
                        order["pl"] = (order["ltp"] - order["entryltp"]) * (order["lots"] * self.lotsize)
                    
                    pl = (pl + order["pl"])

                    # if not self.curExpiry in self.summary:
                    #     self.summary[self.curExpiry] = {}

                    # if not order["index"] in self.summary[self.curExpiry]:
                    #     self.summary[self.curExpiry][order["index"]] = {}

                    # self.summary[self.curExpiry][order["index"]] = {
                    #     "index": order["index"],
                    #     "status": order["active"], 
                    #     "entryDateTime": order["entryDateTime"], 
                    #     "lots": order["lots"], 
                    #     "opr": order["opr"],
                    #     "type": order["type"], 
                    #     "strike": order["strike"], 
                    #     "expiry": order["expiry"], 
                    #     "entryltp": order["entryltp"], 
                    #     "ltp": order["ltp"], 
                    #     "pl": round(order["pl"],2)
                    # }
        
        self.curpl = pl
        # Max profit & Max loss
        if pl > 0 and pl > self.maxprofit :
            self.maxprofit = round(pl,2)

        if pl < 0 and pl < self.maxloss:
            self.maxloss = round(pl,2)

        
                    
    def _orderStatusUpdate(self, opr:str, expiry:str, strike:str, type:str, status:bool):
        opr = opr.upper()
        type = type.upper()
        logging.debug(f"Got request to update {opr} - {type} with strike: {strike}")
        for ordertime in self.orders:
            for orderstrike in self.orders[ordertime]:
                for ordertype in self.orders[ordertime][orderstrike]:
                    order = self.orders[ordertime][orderstrike][ordertype]
                    
                    if order["opr"] == opr and order["type"] == type and order["strike"] == strike:
                        logging.debug(f"Updated {opr} - {type} with strike: {strike}")
                        self.orders[ordertime][orderstrike][ordertype]["active"] = status
                        break

    def _getBreakeven(self, ltp:float):
        credit = 0
        debit = 0
        for time in self.orders:
            for strike in self.orders[time]:
                for type in self.orders[time][strike]:
                    order = self.orders[time][strike][type]
                    
                    # calculate profit & loss
                    if order["opr"] == "S":
                        credit = credit + order["entryltp"]
                    elif  order["opr"] == "B":   
                        debit = debit + order["entryltp"]
        
        # tp - total premium 
        tp = credit - debit
        self.breakeven = { "up": round(ltp + tp), "down": round(ltp - tp), "tp": tp, "credit": credit, "debit": debit }
        logging.info(f'Breakeven updated UP: {self.breakeven["up"]} - Down: {self.breakeven["down"]} ')

    def _table(self, detail = False):
        
        headers = ["Index","Status","Entry Time","Lots","Type","Option", "Strike", "Expiry", "Entry","LTP", "P/L"]
        rows = []
        credit = 0
        debit = 0
        pl = 0
        tp = 0  
        
        for time in self.orders:
            for strike in self.orders[time]:
                for type in self.orders[time][strike]:
                    order = self.orders[time][strike][type]
                    
                    # calculate profit & loss
                    if order["opr"] == "S":
                        credit = round(credit + order["entryltp"],2)
                        order["pl"] = (order["entryltp"] - order["ltp"]) * (order["lots"] * self.lotsize)
                    elif  order["opr"] == "B":   
                        debit = round(debit + order["entryltp"],2)
                        order["pl"] = (order["ltp"] - order["entryltp"]) * (order["lots"] * self.lotsize)
                    
                    pl = (pl + order["pl"])
                    rows.append([order["index"],
                                 order["active"], 
                                 order["entryDateTime"], 
                                 order["lots"], order["opr"],order["type"], order["strike"], order["expiry"], order["entryltp"], order["ltp"], round(order["pl"],2)])

        tp = round((credit - debit),2)
        if detail == True:
            print(tabulate(rows, headers, tablefmt = 'pretty'))

        headers = ["date","Target", "Loss", "Max Profit", "Max Loss", "PL", "PL%"]
        rows = [[self.curExpiry, self.targetedProfit, self.targetedLoss, self.maxprofit, self.maxloss, round(pl,2), str(round((pl * 100) / self.premium,2)) + "%" ]]
        print(tabulate(rows, headers, tablefmt = 'pretty'))

    
    def weekly_short_straddle(self):

        # Rules
        # timeframe weekly 
        # Sell ATM and buy OTM for margin benifit
        # check the breakeven difference should be greater than 200 both side at day end
        # Don't make any entry on expiry day after 12PM
        # Close all the position on expiry day at 3:15PM

        # Estimated premium required with one lots
        estimatedPremium = 56000
        logging.debug(f"Estimated Premium: {estimatedPremium} Lot Size: {self.lotsize} Lots: {self.lots}")
        totalPremium = estimatedPremium * self.lots

        # Targets Profit 
        targetedProfit = round((totalPremium * self.target) / 100)
        targetedLoss = -round((totalPremium * self.loss) / 100)
        logging.debug(f"Total Premium: {totalPremium}, Targeted Profit: {targetedProfit} Targeted Loss: {targetedLoss}")

        # Asigned to global variables
        self.premium = estimatedPremium
        self.targetedProfit = targetedProfit
        self.targetedLoss = targetedLoss

        expiries = self.u._getAllExpiries(self.symbol)
        for i in range(len(expiries)):
            if expiries[i] > self.entryDateTime and expiries[i] < self.exitDateTime:
                entryDateTime = datetime.datetime.strptime(f"{expiries[i]} 15:15:00","%Y-%m-%d %H:%M:%S") 
                curExpiry = datetime.datetime.strptime(f"{expiries[i + 1]} 15:30:00","%Y-%m-%d %H:%M:%S") 

                self.curExpiry = f"{entryDateTime.date()} - {curExpiry.date()}"

                iteration = self.u._getIteration(entryDateTime, curExpiry, 1, True)
                
                # load symbol LTP and Option chain
                self.stockLTP = self.b._getStockLTP(self.symbol, entryDateTime, curExpiry)
                self.optionChain = self.b._getOptionChain(self.symbol, entryDateTime, curExpiry, self.stockLTP)
                
                in_order = False
                sell_atm_diff = 5
                buy_atm_diff = 9

                # clean all orders
                self.count = 0
                self.orders = {}
                self.maxloss = 0
                self.maxprofit = 0

                for t in iteration:
                    if str(t) in self.stockLTP:
                        t = str(t)
                        ltp = self.stockLTP[t]
                        atm_strike = self.u._getATMStrikePrice(ltp, 100)

                        if(in_order == False):
                            sell_call_strike = str(atm_strike + (0 * self.strikeDiff))
                            sell_put_strike = str(atm_strike - (0 * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_call_strike, type="Call", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_put_strike, type="Put", lots= self.lots, opr="S")
                            
                            buy_call_strike = str(atm_strike + (buy_atm_diff * self.strikeDiff))
                            buy_put_strike = str(atm_strike - (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_call_strike, type="Call", lots= self.lots, opr="B")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_put_strike, type="Put", lots= self.lots, opr="B")
                            
                            self._getBreakeven(ltp)
                            in_order = True

                        # here the place where you are putting the logic
                        # if LTP reach to near by break even (call & put) then you need to make the adjustment
                        action_alert = 60
                        breakeven_call_ratio = abs(((self.breakeven["up"] - ltp) * 100) / self.breakeven["tp"])
                        breakeven_put_ratio = abs(((self.breakeven["down"] - ltp) * 100) / self.breakeven["tp"])

                        # Close postion when market going to one direction
                        if breakeven_call_ratio < action_alert:
                            print(f"Call side adjustment required...")
                            self._orderStatusUpdate(opr="S",type="Call", expiry=curExpiry, strike=sell_call_strike, status=False)
                            self._orderStatusUpdate(opr="B",type="Call", expiry=curExpiry, strike=buy_call_strike, status=False)

                            sell_call_strike = str(atm_strike + (sell_atm_diff * self.strikeDiff))
                            buy_call_strike = str(atm_strike + (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_call_strike, type="Call", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_call_strike, type="Call", lots= self.lots, opr="B")
                            
                            # update breakeven
                            self._getBreakeven(ltp)
                            
                        elif breakeven_put_ratio < action_alert:
                            print(f"Put side adjustment required...")
                            self._orderStatusUpdate(opr="S",type="Put", expiry=curExpiry, strike=sell_put_strike, status=False)
                            self._orderStatusUpdate(opr="B",type="Put", expiry=curExpiry, strike=buy_put_strike, status=False)
                            
                            sell_put_strike = str(atm_strike - (sell_atm_diff * self.strikeDiff))
                            buy_put_strike = str(atm_strike - (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_put_strike, type="Put", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_put_strike, type="Put", lots= self.lots, opr="B")

                            # update breakeven
                            self._getBreakeven(ltp)

                        self._orderUpdate(t)
                        # Check targeted Profit and targeted loss 
                        if self.curpl <= self.targetedLoss:
                            logging.info(f"Reached to max loss - Square off all the postions")
                            break
                        
                        # update targeted loss when reached to certain profit
                        


                        

                self._table(True)
                input("Press entry key for continue.....")

    def daily_short_straddle(self):

        # Rules
        # timeframe daily 
        # Sell ATM and buy OTM for margin benifit
        # check the breakeven difference should be greater than 200 both side at day end
        # Don't make any entry on expiry day after 12PM
        # Close all the position on expiry day at 3:15PM

        # Estimated premium required with one lots
        estimatedPremium = 56000
        logging.debug(f"Estimated Premium: {estimatedPremium} Lot Size: {self.lotsize} Lots: {self.lots}")
        totalPremium = estimatedPremium * self.lots

        # Targets Profit 
        targetedProfit = round((totalPremium * self.target) / 100)
        targetedLoss = round((totalPremium * self.loss) / 100)
        logging.debug(f"Total Premium: {totalPremium}, Targeted Profit: {targetedProfit} Targeted Loss: {targetedLoss}")

        expiries = self.u._getAllExpiries(self.symbol)
        for i in range(len(expiries)):
            if expiries[i] > self.entryDateTime and expiries[i] < self.exitDateTime:
                entryDateTime = expiries[i]
                curExpiry = expiries[i + 1]
                iteration = self.u._getIteration(entryDateTime, curExpiry, 1, True)

                # load symbol LTP and Option chain
                self.stockLTP = self.b._getStockLTP(self.symbol, entryDateTime, curExpiry)
                self.optionChain = self.b._getOptionChain(self.symbol, entryDateTime, curExpiry, self.stockLTP)
                
                in_order = False
                sell_atm_diff = 5
                buy_atm_diff = 8

                # clean all orders
                self.count = 0
                self.orders = {}
                self.maxloss = 0
                self.maxprofit = 0
                for t in iteration:
                    if str(t) in self.stockLTP:
                        t = str(t)
                        ltp = self.stockLTP[t]
                        atm_strike = self.u._getATMStrikePrice(ltp, 100)

                        if(in_order == False):
                            sell_call_strike = str(atm_strike + (0 * self.strikeDiff))
                            sell_put_strike = str(atm_strike - (0 * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_call_strike, type="Call", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_put_strike, type="Put", lots= self.lots, opr="S")
                            
                            buy_call_strike = str(atm_strike + (buy_atm_diff * self.strikeDiff))
                            buy_put_strike = str(atm_strike - (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_call_strike, type="Call", lots= self.lots, opr="B")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_put_strike, type="Put", lots= self.lots, opr="B")
                            
                            self._getBreakeven(ltp)
                            in_order = True

                        # here the place where you are putting the logic
                        # if LTP reach to near by break even (call & put) then you need to make the adjustment
                        action_alert = 60
                        breakeven_call_ratio = abs(((self.breakeven["up"] - ltp) * 100) / self.breakeven["tp"])
                        breakeven_put_ratio = abs(((self.breakeven["down"] - ltp) * 100) / self.breakeven["tp"])

                        # Close postion when market going to one direction
                        if breakeven_call_ratio < action_alert:
                            print(f"Call side adjustment required...")
                            self._orderStatusUpdate(opr="S",type="Call", expiry=curExpiry, strike=sell_call_strike, status=False)
                            self._orderStatusUpdate(opr="B",type="Call", expiry=curExpiry, strike=buy_call_strike, status=False)

                            sell_call_strike = str(atm_strike + (sell_atm_diff * self.strikeDiff))
                            buy_call_strike = str(atm_strike + (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_call_strike, type="Call", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_call_strike, type="Call", lots= self.lots, opr="B")
                            
                            # update breakeven
                            self._getBreakeven(ltp)
                            
                        elif breakeven_put_ratio < action_alert:
                            print(f"Put side adjustment required...")
                            self._orderStatusUpdate(opr="S",type="Put", expiry=curExpiry, strike=sell_put_strike, status=False)
                            self._orderStatusUpdate(opr="B",type="Put", expiry=curExpiry, strike=buy_put_strike, status=False)
                            
                            sell_put_strike = str(atm_strike - (sell_atm_diff * self.strikeDiff))
                            buy_put_strike = str(atm_strike - (buy_atm_diff * self.strikeDiff))

                            self._order(entryDateTime=t, expiry=curExpiry, strike=sell_put_strike, type="Put", lots= self.lots, opr="S")
                            self._order(entryDateTime=t, expiry=curExpiry, strike=buy_put_strike, type="Put", lots= self.lots, opr="B")

                            # update breakeven
                            self._getBreakeven(ltp)

                        self._orderUpdate(t)
            
                self._table(True)
                input("Press Enter to continue...")

if __name__=="__main__":

    # Need to check strategy for certain period 
    entryDateTime = datetime.datetime(2023,6,1)
    exitDateTime = datetime.datetime(2023,12,22)

    bt = BackTesting(
        symbol="CNXBAN",
        entryDateTime=entryDateTime, 
        exitDateTime=exitDateTime, 
        target=5,
        loss=2,
        lots=1,
        strategy = "weekly_short_straddle")