from fastapi import FastAPI
from fastapi.responses import JSONResponse

import requests
import json
import pandas as pd

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
        df = pd.read_html(r.content)[3]
        json = df.to_json()
        return JSONResponse(json)
