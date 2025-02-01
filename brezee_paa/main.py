# from typing import Union
import os
import sys
import json
import time
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Database include
from models.database import SessionLocal, engine
from models.tables import Base

Base.metadata.create_all(bind=engine)       

from modules.api.data import data
from modules.api.order import order

nest_asyncio.apply()
app = FastAPI(title='api')

logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(message)s",
        datefmt="%d %b %Y | %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# Load .env file
load_dotenv(".env")

# Calulate time middleware
@app.middleware("executedtime")
async def dispatch(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

# Allowed origins 
origins = ["http://localhost:8000"]
app.add_middleware(CORSMiddleware, allow_origins=origins)

@app.get("/")
async def root() -> dict:
    logging.debug('API is starting up')
    return {
        "status": "ok",
        "code": 200,
        "msg": "Welcome to future !!!"
    }

app.include_router(data)
app.include_router(order)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)