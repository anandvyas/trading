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

    def __init__(self, symbol, entryDateTime, expiry="next", premium=56000, target=5, loss=2, strategy = "weekly_short_straddle") -> None:
        self.b = Breeze()
        self.u = Utility()
        # self.d = Database()

        # get Expiry Date
        self.expiry = self.u._getExpiry(symbol, expiry, entryDateTime)
        
        # get Iteration
        self.iteration = self.u._getIteration(entryDateTime, self.expiry, 1, True)
        
        # load symbol LTP and Option chain
        self.stockLTP = self.b._getStockLTP(symbol, entryDateTime, self.expiry)
        self.optionChain = self.b._getOptionChain(symbol, entryDateTime, self.expiry, self.stockLTP)

        # global variables
        self.count = 0
        self.symbol = symbol.upper()
        self.lotsize = self.u._getLotSize(self.symbol)
        self.ltp = pd.DataFrame([[entryDateTime,0,0,0]],columns=["Datetime","ltp", "EMA5", "EMA20"])
        self.breakeven = {}
        self.target = round((premium * target) / 100)
        self.loss = round((premium * loss) / 100)
        self.orders = {}
        self.maxloss = 0
        self.maxprofit = 0
        self.ratio = {
            "call": [0],
            "put": [0]
        }

        getattr(self, str(strategy), lambda: False)()

    def _order(self, entryDateTime:datetime, strike:str, type:str, lots:int, opr:str):
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
            "expiry": self.expiry,
            "entryltp": self.optionChain[entryDateTime][strike][type]["ltp"],
            "ltp": self.optionChain[entryDateTime][strike][type]["ltp"],
            "pl": 0
        }
        logging.info(f"New order created {opr} {strike} {type}")
        return self.optionChain[entryDateTime][strike][type]["ltp"]
    
    def _orderStatusUpdate(self, opr:str, strike:str, type:str, status:bool):
        opr = opr.upper()
        type = type.upper()
        logging.info(f"Got request to update {opr} - {type} with strike: {strike}")
        for ordertime in self.orders:
            for orderstrike in self.orders[ordertime]:
                for ordertype in self.orders[ordertime][orderstrike]:
                    order = self.orders[ordertime][orderstrike][ordertype]
                    
                    if order["opr"] == opr and order["type"] == type and order["strike"] == strike:
                        logging.info(f"Updated {opr} - {type} with strike: {strike}")
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

    def _table(self, curTime:datetime, detail = False):
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
                    
                    # update order ltp
                    if order["active"] == True and self.optionChain[curTime][strike][type]["ltp"] > 0:
                        order["ltp"] = self.optionChain[curTime][strike][type]["ltp"]

                    # calculate profit & loss
                    if order["opr"] == "S":
                        credit = round(credit + order["entryltp"],2)
                        order["pl"] = (order["entryltp"] - order["ltp"]) * (order["lots"] * self.lotsize)
                    elif  order["opr"] == "B":   
                        debit = round(debit + order["entryltp"],2)
                        order["pl"] = (order["ltp"] - order["entryltp"]) * (order["lots"] * self.lotsize)
                    
                    pl = (pl + order["pl"])
                    rows.append([order["index"],order["active"], order["entryDateTime"], order["lots"], order["opr"],order["type"], order["strike"], order["expiry"], order["entryltp"], order["ltp"], round(order["pl"],2)])

        # Max profit & Max loss
        if pl > 0 and pl > self.maxprofit :
            self.maxprofit = pl

        if pl < 0 and pl < self.maxloss:
            self.maxloss = pl

        tp = round((credit - debit),2)
        if detail == True:
            print(tabulate(rows, headers, tablefmt = 'pretty'))

        headers = ["Date", "LTP", "BE-Down", "BE-UP","Call-R", "Put-R", "Credit", "Debit", "TP", "Target", "Loss", "Max Profit", "Max Loss", "PL"]
        rows = [[curTime, 
                 self.stockLTP[curTime], 
                 self.breakeven["down"], 
                 self.breakeven["up"],
                 self.ratio["call"][-1],
                 self.ratio["put"][-1], 
                 credit, debit, tp, self.target, self.loss, self.maxprofit, self.maxloss, round(pl,2) ]]
        print(tabulate(rows, headers, tablefmt = 'pretty'))
        

    def weekly_short_straddle(self):
        # Rules
        # timeframe weekly 
        # Sell ATM and buy OTM for margin benifit
        # check the breakeven difference should be greater than 200 both side at day end
        # Don't make any entry on expiry day after 12PM
        # Close all the position on expiry day at 3:15PM



        in_order = False
        lots = 1
        sell_atm_diff = 5
        buy_atm_diff = 7
        strike_diff = 100
        adjustment = { 
            "call": 0, 
            "put": 0
        }
        call_side_adjustment = False
        put_side_adjustment = False

        for t in self.iteration:
            if str(t) in self.stockLTP:
                t = str(t)
                ltp = self.stockLTP[t]
                atm_strike = self.u._getATMStrikePrice(ltp, 100)

                self.ltp.loc[len(self.ltp.index)] = [t, ltp, 0 , 0]
                self.ltp["EMA5"] = ta.ema(self.ltp["ltp"], length=5)
                self.ltp["EMA20"] = ta.ema(self.ltp["ltp"], length=20)

                if(in_order == False):
                    sell_call_strike = str(atm_strike + (0 * strike_diff))
                    sell_put_strike = str(atm_strike - (0 * strike_diff))

                    self._order(t, sell_call_strike, "Call", lots, "s")
                    self._order(t, sell_put_strike, "Put", lots, "s")

                    buy_call_strike = str(atm_strike + (buy_atm_diff * strike_diff))
                    buy_put_strike = str(atm_strike - (buy_atm_diff * strike_diff))

                    self._order(t, buy_call_strike, "Call", lots, "b")
                    self._order(t, buy_put_strike, "Put", lots, "b")
                    
                    self._getBreakeven(ltp)
                    in_order = True
                    
                # here the place where you are putting the logic
                # if LTP reach to near by break even (call & put) then you need to make the adjustment
                action_alert = 50
                breakeven_call_ratio = abs(((self.breakeven["up"] - ltp) * 100) / self.breakeven["tp"])
                breakeven_put_ratio = abs(((self.breakeven["down"] - ltp) * 100) / self.breakeven["tp"])
                
                self.ratio["call"].append(round(breakeven_call_ratio,2))
                self.ratio["put"].append(round(breakeven_put_ratio,2))
                
                # Close postion when market going to one direction
                if breakeven_call_ratio < action_alert:
                    print(f"Call side adjustment required...")
                    self._orderStatusUpdate(opr="S",type="Call",strike=sell_call_strike, status=False)
                    self._orderStatusUpdate(opr="B",type="Call",strike=buy_call_strike, status=False)

                    sell_call_strike = str(atm_strike + (sell_atm_diff * strike_diff))
                    buy_call_strike = str(atm_strike + (buy_atm_diff * strike_diff))

                    self._order(t, sell_call_strike, "Call", lots, "S")
                    self._order(t, buy_call_strike, "Call", lots, "B")
                    
                    # update breakeven
                    self._getBreakeven(ltp)

                    # self._table(t, True)
                    # input("Press Enter to continue...")
                    
                elif breakeven_put_ratio < action_alert:
                    print(f"Put side adjustment required...")
                    self._orderStatusUpdate(opr="S",type="Put",strike=sell_put_strike, status=False)
                    self._orderStatusUpdate(opr="B",type="Put",strike=buy_put_strike, status=False)
                    
                    sell_put_strike = str(atm_strike - (sell_atm_diff * strike_diff))
                    buy_put_strike = str(atm_strike - (buy_atm_diff * strike_diff))

                    self._order(t, sell_put_strike, "Put", lots, "S")
                    self._order(t, buy_put_strike, "Put", lots, "B")
                    
                    # update breakeven
                    self._getBreakeven(ltp)

                    # self._table(t, True)
                    # input("Press Enter to continue...")
                
                
                self._table(t, True)
            # input("Press Enter to continue...")

# 3JAN2019,10JAN2019,17JAN2019,24JAN2019,31JAN2019,7FEB2019,14FEB2019,21FEB2019,28FEB2019,7MAR2019,14MAR2019,20MAR2019,28MAR2019,4APR2019,11APR2019,18APR2019,25APR2019,2MAY2019,9MAY2019,16MAY2019,23MAY2019,30MAY2019,6JUN2019,13JUN2019,20JUN2019,27JUN2019,4JUL2019,11JUL2019,18JUL2019,25JUL2019,1AUG2019,8AUG2019,14AUG2019,22AUG2019,29AUG2019,26SEP2019,5SEP2019,12SEP2019,19SEP2019,31OCT2019,3OCT2019,10OCT2019,17OCT2019,24OCT2019,28NOV2019,7NOV2019,14NOV2019,21NOV2019,26DEC2019,5DEC2019,12DEC2019,19DEC2019
# 30JAN2020,2JAN2020,9JAN2020,16JAN2020,23JAN2020,27FEB2020,6FEB2020,13FEB2020,20FEB2020,26MAR2020,5MAR2020,12MAR2020,19MAR2020,30APR2020,1APR2020,9APR2020,16APR2020,23APR2020,7MAY2020,28MAY2020,14MAY2020,21MAY2020,25JUN2020,4JUN2020,11JUN2020,18JUN2020,30JUL2020,2JUL2020,9JUL2020,16JUL2020,23JUL2020,27AUG2020,6AUG2020,13AUG2020,20AUG2020,24SEP2020,3SEP2020,10SEP2020,17SEP2020,1OCT2020,29OCT2020,8OCT2020,15OCT2020,22OCT2020,5NOV2020,26NOV2020,12NOV2020,19NOV2020,3DEC2020,31DEC2020,10DEC2020,17DEC2020,24DEC2020
# 7JAN2021,28JAN2021,14JAN2021,21JAN2021,4FEB2021,25FEB2021,11FEB2021,18FEB2021,4MAR2021,25MAR2021,10MAR2021,18MAR2021,1APR2021,29APR2021,8APR2021,15APR2021,22APR2021,6MAY2021,27MAY2021,12MAY2021,20MAY2021,3JUN2021,24JUN2021,10JUN2021,17JUN2021,1JUL2021,29JUL2021,8JUL2021,15JUL2021,22JUL2021,5AUG2021,30SEP2021,26AUG2021,12AUG2021,18AUG2021,2SEP2021,9SEP2021,16SEP2021,23SEP2021,7OCT2021,28OCT2021,14OCT2021,21OCT2021,3NOV2021,25NOV2021,11NOV2021,18NOV2021,2DEC2021,30DEC2021,9DEC2021,16DEC2021,23DEC2021
# 6JAN2022,27JAN2022,13JAN2022,20JAN2022,3FEB2022,24FEB2022,10FEB2022,17FEB2022,3MAR2022,31MAR2022,10MAR2022,17MAR2022,24MAR2022,7APR2022,28APR2022,13APR2022,21APR2022,5MAY2022,26MAY2022,12MAY2022,19MAY2022,2JUN2022,30JUN2022,9JUN2022,16JUN2022,23JUN2022,7JUL2022,28JUL2022,14JUL2022,21JUL2022,4AUG2022,25AUG2022,11AUG2022,18AUG2022,1SEP2022,29SEP2022,8SEP2022,15SEP2022,22SEP2022,6OCT2022,27OCT2022,13OCT2022,20OCT2022,3NOV2022,24NOV2022,10NOV2022,17NOV2022,1DEC2022,29DEC2022,8DEC2022,15DEC2022,22DEC2022

if __name__=="__main__":
    
    entryDateTime = datetime.datetime(2022,1,6,15,15,0)
    bt = BackTesting(
        symbol="CNXBAN",
        entryDateTime=entryDateTime, 
        expiry="next", 
        premium = 56000,
        target=5,
        loss=2,
        strategy = "weekly_short_straddle")