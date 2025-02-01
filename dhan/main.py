import json
import os
import sys
import gc
import logging
from modules.dhan import Dhan
from modules.shoonya import ShoonyaApiPy

logging.basicConfig(level=logging.DEBUG)

# dhan = Dhan()
shoonya = ShoonyaApiPy()

# login with Shoonya
ret = shoonya.login(userid=os.getenv("SHO_USER"), password=os.getenv("SHO_PASSWORD"), 
                    twoFA=os.getenv("SHO_2FACTOR"), vendor_code=os.getenv("SHO_VENDOR_CODE"), 
                    api_secret=os.getenv("SHO_API_SECRET"), imei=os.getenv("SHO_IMEI"))

print(ret)

# print(dhan.getAvailableFunds())