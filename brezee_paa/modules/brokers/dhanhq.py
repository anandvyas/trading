import json
import os
import sys
import gc
import logging
from datetime import datetime
from time import time, sleep
from os.path import join, dirname
from dhanhq import dhanhq
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

from .broker import BrokerInterface

class Dhan(BrokerInterface):
    def __init__(self) -> None: 
        self.dhan = dhanhq(os.getenv("DHAN_CLIENT_ID"), os.getenv("DHAN_ACCESS_TOKEN"))
        
    def _getAvailableFunds(self):
        funds = self.dhan.get_fund_limits()
        return funds
    
    def quote(self, stock_code:str):
            stock_code = stock_code.upper()
            query = { "symbols": stock_code }
            rs = self.fyers.quotes(query)
            if rs['d'][0]['s'] == 'error':
                return None
            else:
                 return rs['d'][0]['v']['cmd']['c']