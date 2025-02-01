import os
import logging
import requests
import json, datetime
import pandas as pd
from datetime import date, time, timedelta
from fastapi import APIRouter, HTTPException, Depends

from modules.utility import Utility
from modules.brokers.broker import Broker

from typing import Annotated
from pydantic import BaseModel

u = Utility()
b = Broker()

data = APIRouter(
    prefix="/data",
    tags=["Data"]
)

@data.get("/")
async def index():
    return {
            "status": "ok",
            "code": 200,
            "result": "Welcome to Data API"
        }

@data.get("/holidays")
async def holidays():
    holidays = b._getHolidays()
    if holidays == None:
        raise HTTPException(status_code=404, detail="Holiday file not found")
    return {
        "status": "ok",
        "code": 200,
        "result": holidays
    }
    
@data.get("/brokers")
async def brokers():
    brokers = b._getBrokers()
    if brokers == None:
        raise HTTPException(status_code=404, detail="Brokers file not found")
    return {
        "s": "ok",
        "c": 200,
        "result": brokers
    }
    
@data.get("/status")
async def status():
    return {
        "status": "ok",
        "code": 200,
        "result": b._isMarketActive()
    }

def getDataAPIProvider():
    pass

class Symbol(BaseModel):
    symbol: str | None = "Nifty"

class SymbolList(BaseModel):
    symbols: list[Symbol]

@data.post("/expiries")
async def expiries(params: Symbol, broker : object = Depends(getDataAPIProvider)):
    """
    All the expiries of provided Index symbol
    """
    # change the symbol in uppercase
    params.symbol = params.symbol.upper()

    # get the list of all the indices and validate 
    indices = b._getIndices()
    if params.symbol not in indices:
        raise HTTPException(status_code=404, detail=f" {params.symbol} not a valid Indices ")
    
    expiries = b._getExpiries(params.symbol)
    return {
            "s": "ok",
            "c": 200,
            "result": {
                "symbol": params.symbol,
                "expiries": expiries
            }
        }

class Expiry(BaseModel):
    symbol: str | None = "Nifty"
    expiry: str | None = "current"

@data.post("/expiry")
async def expiry(params: Expiry, broker : object = Depends(getDataAPIProvider)):
    """
    Provide expiry of Index symbol based on args passed (current, next and far)
    """
    # change the symbol in uppercase
    params.symbol = params.symbol.upper()

    # get the list of all the indices and validate 
    indices = u._getIndices()
    if params.symbol not in indices:
        raise HTTPException(status_code=404, detail=f" {params.symbol} not a valid Indices ")
    
    if params.expiry not in ["current","next","far"]:
            params.expiry = "next" 

    expiries = broker._getExpiry(params.symbol, params.expiry)
    return {
            "s": "ok",
            "c": 200,
            "result": {
                "symbol": params.symbol,
                "term": params.expiry,
                "expiries": expiries
            }
        }

@data.post("/quote")
async def quotes(params: Symbol, broker : object = Depends(getDataAPIProvider)):
    # change the symbol in uppercase
    params.symbol = params.symbol.upper()

    # get the list of all the indices/equity and validate 
    symbols = b._getAllSymbols()
    if params.symbol not in symbols:
        raise HTTPException(status_code=404, detail=f" {params.symbol} not a valid Indices/Equity ")
    
    # get the actual symbol based on Broker 
    symbol = b._getBrokerSymbol(params.symbol)
    
    quotes = b.quote(symbol[b.dataProvider]) 
    return {
            "s": "ok",
            "c": 200,
            "result": {
                "symbol": symbol[broker.name],
                "broker": broker.name,
                "ltp": quotes
            }
        }

@data.post("/strike")
async def strike(params: Symbol, broker : object = Depends(getDataAPIProvider)):
    # change the symbol in uppercase
    params.symbol = params.symbol.upper()

    # get the list of all the indices and validate 
    indices = u._getIndices()
    if params.symbol not in indices:
        raise HTTPException(status_code=404, detail=f" {params.symbol} not a valid Indices ")
    
    # get the actual symbol based on Broker 
    symbol = u._getBrokerSymbol(params.symbol)
    
    # Get the LTP 
    ltp = broker.quotes(symbol[broker.name]) 
    atmStrike = u._getATMStrikePrice(ltp, symbol["STRIKEDIFF"])
    strikes = u._getStrikes(atmStrike, symbol["STRIKEDIFF"], 25)

    return {
            "s": "ok",
            "c": 200,
            "result": {
                "symbol": symbol[broker.name],
                "broker": broker.name,
                "ltp": ltp,
                "atm": atmStrike,
                "strikes": strikes
            }
        }

class Historical(BaseModel):
    symbol: str | None = "Nifty"
    resolution: str | None = "1min"
    range_from: str | None = (datetime.datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    range_to: str | None = datetime.datetime.today().strftime("%Y-%m-%d")

@data.post("/historical")
async def historical(params: Historical, 
                     broker : object = Depends(getDataAPIProvider)):
    # change the symbol in uppercase
    params.symbol = params.symbol.upper()

    # get the list of all the indices/equity and validate 
    symbols = u._getAllSymbols()
    if params.symbol not in symbols:
        raise HTTPException(status_code=404, detail=f" {params.symbol} not a valid Indices/Equity ")
    
    # get the actual symbol based on Broker 
    symbol = u._getBrokerSymbol(params.symbol) 

    resolutions = ["1min","3min","5min","10min","15min","30min","hour","day","week","month"]
    if params.resolution not in resolutions:
        raise HTTPException(status_code=404, detail=f" {params.resolution} not a valid time frame ")
    
    data = broker.historical(symbol[broker.name], 
                             params.resolution, 
                             params.range_from, 
                             params.range_to)

    return {
            "s": "ok",
            "c": 200,
            "result": {
                "symbol": symbol[broker.name],
                "broker": broker.name,
                "range_from": params.range_from,
                "range_to": params.range_to,
                "data": data
            }
        }