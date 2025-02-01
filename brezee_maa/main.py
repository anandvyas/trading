from modules.utility import Utility
from modules.strategies import Strategies

if __name__=="__main__":

    s = Strategies(client="fyers", 
                   symbol="BANKNIFTY", 
                   strategy="weekly_short_straddle", 
                   lots=1,
                   targetedProfit=5,
                   targetedLoss=2)
    pass