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

class Dhan:
    def __init__(self) -> None:
        self.dhan = dhanhq(os.getenv("clientid"), os.getenv("accessToken"))

    def getAvailableFunds(self):
        return self.dhan.get_fund_limits()