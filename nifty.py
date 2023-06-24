
import datetime
import requests
import json
import pandas as pd
import mibian
from scipy.stats import norm 

def fetch_nifty(exdate):

    date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Accept-Language': 'en, gu;q=0.9, hi;q=0.8','Accept-Encoding': 'gzip, deflate, br'}

    url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
    r = requests.get(url, headers=headers, timeout=5)

    if r.status_code == 401:
        return "Error 401"
    else:
        temp_df = pd.DataFrame(columns = ['type','strikePrice','expiryDate','underlying', 'openInterest', 'changeinOpenInterest','totalTradedVolume','impliedVolatility',
                                'lastPrice','change','underlyingValue'])

        data = json.loads(r.text)['records']['data']    
        tl = [item for item in data if (item['expiryDate'] == exdate )]

        for i in tl:
            if 'CE' in i:
                ce = ['CE',i['CE']['strikePrice'],i['CE']['expiryDate'],i['CE']['underlying'],i['CE']['openInterest'],i['CE']['changeinOpenInterest'],
                    i['CE']['totalTradedVolume'],i['CE']['impliedVolatility'],i['CE']['lastPrice'],i['CE']['change'],i['CE']['underlyingValue']]
    
                temp_df.loc[len(temp_df)] = ce

            if 'PE' in i: 
                pe = ['PE',i['PE']['strikePrice'],i['PE']['expiryDate'],i['PE']['underlying'],i['PE']['openInterest'],i['PE']['changeinOpenInterest'],
                    i['PE']['totalTradedVolume'],i['PE']['impliedVolatility'],i['PE']['lastPrice'], i['PE']['change'], i['PE']['underlyingValue']]

                temp_df.loc[len(temp_df)] = pe

        temp_df = temp_df.apply(process_row, axis=1)
        df = temp_df[~temp_df['should_remove']]
        df = patch(df)

        return df

#dependencies process row, compute greeks, patch greeks in df


def process_row(row):

    # Calculate 'count_new' column
    strike = row['strikePrice']
    atm = round(row['underlyingValue'] / 50) * 50
    row['count'] = (strike - atm) / 100

    # Calculate 'dte' column
    expiry = datetime.datetime.strptime(row['expiryDate'], '%d-%b-%Y').date()
    today = datetime.datetime.today().date()
    row['dte'] = (expiry - today).days

    # Calculate 'should_remove' column
    if (row['count'] < -1 and row['type'] == 'CE') or (row['count'] > 10 and row['type'] == 'CE') : row['should_remove'] = True
    elif (row['count'] > 1 and row['type'] == 'PE') or (row['count'] < -10 and row['type'] == 'PE') : row['should_remove'] = True
    else:
        row['should_remove'] = False
    return row

def compute_greeks(row):
    greeks = {}
    spot = round(row['underlyingValue'],2)
    strike = int(row['strikePrice'])
    days = int(row['dte'])
    rate = 10
    price = int(row['lastPrice'])

    #Calculate Volatility first and then greeks

    if row["type"] == "CE":
        vol = mibian.BS([spot,strike,rate,days], callPrice=price).impliedVolatility
        g = mibian.BS([spot,strike,rate,days], volatility=vol)
        
        greeks["Delta"] = g.callDelta.round(2)
        greeks["Theta"] = g.callTheta.round(2)
        greeks["IV"] = vol
        greeks["Vega"] = g.vega.round(2)

        
    else:
        vol = mibian.BS([spot,strike,rate,days], putPrice=price).impliedVolatility
        g = mibian.BS([spot, strike,rate,days], volatility=vol)
        
        greeks["Delta"] = g.putDelta.round(2)
        greeks["Theta"] = g.putTheta.round(2)
        greeks["IV"] = vol
        greeks["Vega"] = g.vega.round(2)
        
    return greeks


def patch(df):
    # Calculate the Greeks once for each row and store the results in a temporary variable
    df['Greeks'] = df.apply(lambda row: compute_greeks(row), axis=1)

    # Extract the desired values from the temporary variable and assign them to new columns
    df['Delta'] = df['Greeks'].apply(lambda greeks: greeks['Delta'])
    df['Vega'] = df['Greeks'].apply(lambda greeks: greeks['Vega'])
    df['Theta'] = df['Greeks'].apply(lambda greeks: greeks['Theta'])
    df['IV'] = df['Greeks'].apply(lambda greeks: greeks['IV'])

    # Drop the temporary column containing the Greeks
    df = df.drop('Greeks', axis=1)

    return df    

