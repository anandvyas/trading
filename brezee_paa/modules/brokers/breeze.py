import os
import logging
import urllib
import pandas as pd
import nest_asyncio
from dotenv import load_dotenv

from pyotp import TOTP
import asyncio
from pyppeteer import launch
from breeze_connect import BreezeConnect

from .broker import BrokerInterface

nest_asyncio.apply()
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)

api_key =  os.environ.get("BREEZE_API_KEY")
secret_key = os.environ.get("BREEZE_SECRET_KEY")
session_token = os.environ.get("BREEZE_SESSION")

class Breeze(BrokerInterface):

    # constructor
    def __init__(self, salt='SlTKeYOpHygTYkP3') -> None:
        self.breeze = BreezeConnect(api_key=api_key)
        self._login()
        pass

    def quote(self, symbol):
        pass

    def _getOptionChain(self, stock_code:str, expiry = "next"):
        try:
            expiry = self._getExpiry(stock_code.upper(),expiry)
            allowColumns = ["strike_price","ltp","open_interest","total_quantity_traded","total_buy_qty","total_sell_qty"]
            
            occ = self.breeze.get_option_chain_quotes(stock_code=stock_code.upper(),
                                                 exchange_code="NFO",
                                                 product_type="options",
                                                 expiry_date=expiry,
                                                 right="call")["Success"]
            
            df = pd.DataFrame(occ,columns=allowColumns)
            df.index = df['strike_price']
            df = df.add_prefix("call_")
            
            ocp = self.breeze.get_option_chain_quotes(stock_code=stock_code.upper(),
                                                 exchange_code="NFO",
                                                 product_type="options",
                                                 expiry_date=expiry,
                                                 right="put")["Success"]
            
            df2 = pd.DataFrame(ocp,columns=allowColumns)
            df2.index = df2['strike_price']
            df2 = df2.add_prefix("put_")
            
            return pd.merge(df, df2, left_index=True, right_index=True)
        except Exception as e:
            logging.error(str(e))

    def _login(self):
        try:
            self.breeze.generate_session(api_secret=secret_key,session_token=session_token)
            logging.info(f"ICICI Breeze login successfully...")
            self.user = self.breeze.get_customer_details(api_session=session_token)["Success"]
            logging.info(f"Welcome {self.user['idirect_user_name']}")

        except Exception as e:
            logging.debug(f"ICICI Breeze session not valid...")
            logging.debug(f"Initiate new session request")
            asyncio.get_event_loop().run_until_complete(self._getSession())
            
    async def _getSession(self):
        logging.debug(f"ICICI Breeze login initiated")
        # login to ICICI Breeze
        url = "https://api.icicidirect.com/apiuser/login?api_key=" + urllib.parse.quote_plus(os.environ.get("BREEZE_API_KEY"))
        browserObj = await launch({'headless': True})
        site = await browserObj.newPage()
        await site.goto(url)
        await site.waitFor(1000)

        await site.waitForSelector("#txtuid")
        await site.type('#txtuid', os.environ.get("BREEZE_USER"))
        await site.waitForSelector("#txtPass")
        await site.type('#txtPass', os.environ.get("BREEZE_PASS"))
        checkboxEl = await site.waitForSelector("#chkssTnc")
        await checkboxEl.click()

        # Submit the form
        await site.keyboard.press('Enter')
        await site.waitFor(1000)

        # Manage TOTP
        totp = TOTP(os.environ.get("BREEZE_TOTP"))
        token = totp.now()
        await site.waitForSelector("#hiotp")
        await site.type("#hiotp", token)

        await site.waitForSelector("#Button1")
        await site.click('#Button1')
        await site.waitFor(1000)

        session = site.url #.split("apisession=")[1][:8]
        print(session)
        exit()
        await site.waitFor(10000)
        await browserObj.close()
        
        return session