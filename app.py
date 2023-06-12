from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import requests
import pandas as pd

import yfinance as yf
from datetime import datetime

app = FastAPI()

@app.get("/")

def first_api():
        return {'message': 'Hello Vinod'}


BOOKS = [{"title": 'Title 1'},{"title": 'Title 2'},{"title": 'Title 3'}]

@app.get("/books")

def read_books():
        return BOOKS


@app.get("/nifty50")

def get_nifty50():
        r = requests.get("https://en.wikipedia.org/wiki/NIFTY_50")
        df = pd.read_html(r.content)[2]
        return jsonable_encoder(df)


@app.get("/price/")

def get_price_by_symbol(symbol:str,start:str,end:str):
        #date input format is "YYYY-MM-DD"
        df = yf.download(symbol,start=start,end=end)
        df_json = df.to_dict(orient='records')
        return df_json
