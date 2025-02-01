import os
import json
from textwrap import indent
from tkinter import NS
import pandas as pd
from urllib.parse import urlparse, parse_qs
from os.path import join, dirname
from dotenv import load_dotenv
from datetime import date
import asyncio
from pyppeteer import launch

from modules.nse  import NSE

# Fyers API
from fyers_api import fyersModel
from fyers_api import accessToken
from fyers_api.Websocket import ws

# Read env values
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

fyers_client_id = os.environ.get("FYR_CLIENT_ID")
fyers_password = os.environ.get("FYR_PASSWORD")
app_id = os.environ.get("FYR_APP_ID")
secret_key = os.environ.get("FYR_SECRET_KEY")


class Fyers:

    def __init__(self) -> None:
        logPath = f"{dirname(__file__)}/../logs"
        
        access_token = self._getAccessToken()
        self.fyers = fyersModel.FyersModel(token=access_token, log_path=logPath, client_id=app_id)
        self.fyers.token = access_token

    def _getWSToken(self):
        logPath = f"{dirname(__file__)}/../logs"
        access_token = f"{app_id}:{self._getAccessToken()}"
        return ws.FyersSocket(access_token=access_token,run_background=False,log_path=logPath)


    def _getQuotes(self, symbol = ["NSE:NIFTY50-INDEX", "NSE:SBIN-EQ"]):
        try:
            data = self.fyers.quotes({"symbols": symbol})
            return data
        except Exception as e:
            return False

    def _getLtp(self, symbol = "NSE:NIFTY50-INDEX"):
        try:
            data = self.fyers.quotes({"symbols": symbol})
            return data['d'][0]['v']['lp']
        except Exception as e:
            return str(e)

    def _getAccessToken(self):

        currentDate = date.today()
        tokenFile = f"{dirname(__file__)}/../tmp/{currentDate.strftime('%d-%m-%Y')}.json"

        if os.path.exists(tokenFile):
            f = open (tokenFile, "r")
            json_object = json.loads(f.read())
            return json_object['access_token']
        else:
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(self._login())
            
            appSession = accessToken.SessionModel(client_id= app_id, secret_key = secret_key, grant_type="authorization_code")
            appSession.set_token(res['auth_code'][0])
            access_token =  appSession.generate_token()

            access_token = json.dumps(access_token)

            with open(tokenFile, "w") as outfile:
                outfile.write(access_token)
            
            return self._getAccessToken()

    async def _login(self):

        session = accessToken.SessionModel(client_id = app_id, 
                                                secret_key = secret_key,
                                                redirect_uri='https://www.google.com', 
                                                response_type='code', 
                                                grant_type='authorization_code', 
                                                state=None)

        loop = asyncio.get_event_loop()
        url = session.generate_authcode() 

        browser = await launch({ "headless": True, "executablePath": '/usr/bin/google-chrome', "args": ['--no-sandbox'] })
        page = await browser.newPage()

        await page.goto(url)

        # inset client ID
        await page.type('#fy_client_id', fyers_client_id)
        await page.click('#clientIdSubmit')
        await page.waitFor(1000)

        # inset client password
        await page.type('#fy_client_pwd', fyers_password)
        await page.click('#loginSubmit')
        await page.waitFor(1000)

        # insert PIN 
        await page.type('#first', "5")
        await page.type('#second', "8")
        await page.type('#third', "7")
        await page.type('#fourth', "4")
        await page.click('#verifyPinSubmit')
        await page.waitFor(5000)

        response = parse_qs(page.url)
        # await page.screenshot({'path': 'oxylabs_python.png'})
        await browser.close()

        return response




