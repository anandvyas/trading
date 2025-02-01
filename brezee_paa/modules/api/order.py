import os
import logging
import requests
import json, datetime
import pandas as pd
from datetime import date, time
from fastapi import APIRouter, HTTPException, Depends

from modules.utility import Utility
from modules.telegram import TG

from typing import Annotated
from pydantic import BaseModel

u = Utility()
t = TG()

order = APIRouter(
    prefix="/order",
    tags=["Order"]
)

def getActiveBroker():
    # select default data api provider Broker
    provider = u._get("activeBroker")
    if provider == None:
        raise HTTPException(status_code=404, detail="Default data api provider not defined")
    
    logging.debug(f'Active Broker: {provider}')
    return eval(provider.title())()

@order.get("/")
async def index(broker : object = Depends(getActiveBroker)):
    return {
            "status": "ok",
            "code": 200,
            "result": "Welcome to Order API"
        }

@order.get("/funds")
async def index(broker : object = Depends(getActiveBroker)):
    funds = broker._getAvailableFunds()
    return {
            "status": "ok",
            "code": 200,
            "funds": funds
        }

@order.post("/")
async def index():
    return {
            "status": "ok",
            "code": 200,
            "result": "Welcome to Order API"
        }