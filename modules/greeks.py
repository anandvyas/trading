from datetime import datetime, timedelta 
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.implied_volatility import *
from py_vollib.black_scholes.greeks.analytical import delta, gamma, vega, theta, rho

class GREEKS:

    '''
    :param price: float: option price
    :param S: float: underlying asset price
    :param K: float: Strike price
    :param t: float: time to expiration in years
    :param r: float: risk-free interest rate
    :param flag: str: 'c' or 'p' for call or put.
    '''

    def __init__(self) -> None:
        pass

    def iv(self, price, S, K, t, r = 0.1, flag = 'c'):
        t = t - datetime.now() # datetime(2022,8,8,15,30)
        t = t/timedelta(days=1)
        t = t/365

        return round(implied_volatility(price, S, K, t, r , flag) * 100, 2)