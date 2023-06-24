from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


import yfinance as yf
from datetime import datetime


import datetime
import requests
import json
import pandas as pd
import mibian

app = FastAPI()

@app.get("/")

def first_api():
        return {'message': 'Hello Vinod'}

BOOKS = [{"title": 'Title 1'},{"title": 'Title 2'},{"title": 'Title 3'}]

from nifty import fetch_nifty, compute_greeks, patch,process_row

@app.get("/nifty")

def nifty():
        df = fetch_nifty("29-Jun-2023")
        df_json = df.to_dict(orient='records')
        return df_json



@app.get("/nifty50")

def get_nifty50():
        r = requests.get("https://en.wikipedia.org/wiki/NIFTY_50")
        df = pd.read_html(r.content)[2]
        df_json = df.to_dict(orient='records')
        return df_json


@app.get("/price/")

def get_price_by_symbol(symbol:str,start:str,end:str):
        #date input format is "YYYY-MM-DD"
        df = yf.download(symbol,start=start,end=end)
        df_json = df.to_dict(orient='records')
        return df_json
