import os
import logging
import requests
import pandas as pd
from time import time, sleep
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from pyotp import TOTP

from dhanhq import dhanhq

from modules.utility import Utility

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

client_id = os.environ.get("DHAN_CLIENT_ID") 
access_token = os.environ.get("DHAN_ACCESS_TOKEN") 

class Dhan():

    def __init__(self) -> None:
        self.dhan = dhanhq(client_id,access_token)
        funds = self.dhan.get_fund_limits()

        holding = self.dhan.get_holdings()
        print(holding)

        pass
