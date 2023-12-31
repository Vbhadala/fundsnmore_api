from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


import yfinance as yf
from datetime import datetime

import datetime
import requests
import json
import pandas as pd
pd.set_option('mode.chained_assignment', None)
import mibian

app = FastAPI()

@app.get("/")

def first_api():
        return {'message': 'Hello Vinod'}


from nifty import fetch_nifty, compute_greeks, patch,process_row, operation,calculate_max_pain

@app.get("/nifty/{dynamic_param}")

def nifty(dynamic_param : str):
        r = fetch_nifty(dynamic_param)
        df_chain_json = r[0].to_dict(orient='records')
        return df_chain_json
    
@app.get("/nifty_greeks/{dynamic_param}")

def nifty(dynamic_param : str):
        r = fetch_nifty(dynamic_param)
        df_ops_json = r[1].to_dict(orient='records')
        return df_ops_json

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
