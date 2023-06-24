
import datetime
import requests
import json
import pandas as pd
import mibian

def fetch_nifty(exdate):

    date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'Accept-Language': 'en, gu;q=0.9, hi;q=0.8','Accept-Encoding': 'gzip, deflate, br'}
    
    
    url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
    r = requests.get(url, headers=headers, timeout=5)
 
    if r.status_code == 401:
        print("Error 401")
    
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
        
        greek_df = operation(df)

        return df, greek_df

    
    
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
    if (row['count'] < -1 and row['type'] == 'CE') or (row['count'] > 10 and row['type'] == 'CE'):
        row['should_remove'] = True
    elif (row['count'] > 1 and row['type'] == 'PE') or (row['count'] < -10 and row['type'] == 'PE'):
        row['should_remove'] = True
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
        greeks["IV"] = round(vol,2)
        greeks["Vega"] = g.vega.round(2)
       
        
    else:
        vol = mibian.BS([spot,strike,rate,days], putPrice=price).impliedVolatility
        g = mibian.BS([spot, strike,rate,days], volatility=vol)
        
        greeks["Delta"] = g.putDelta.round(2)
        greeks["Theta"] = g.putTheta.round(2)
        greeks["IV"] = round(vol,2)
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


def operation(df):

    max_pain = calculate_max_pain(df)
    ce_df = df[df['type'] == 'CE']
    pe_df = df[df['type'] == 'PE']

    # Create a new DataFrame with the desired columns and their sums
    greek_df = pd.DataFrame({
        'underlying': [df['underlyingValue'].iloc[0]],  # Assuming the 'underlyingValue' is constant for all rows
        'expiryDate': [df['expiryDate'].iloc[0]],
        'dte': [df['dte'].iloc[0]], # Assuming the 'expiryDate' is constant for all rows
        'atmStrike': [df[df['count'] == 0 ]['strikePrice'].iloc[0]],
        'atmIV': [df[df['count'] == 0 ]['IV'].sum()/2],
        'atmStraddle': [df[df['count'] == 0 ]['lastPrice'].sum().round(2)],
        'atmStrangle': [df[(df['count'] == 0.5) & (df['type'] == 'CE')]['lastPrice'].sum().round(2) + df[(df['count'] == -0.5) & (df['type'] == 'PE')]['lastPrice'].sum().round(2)],
        'OI': [df['openInterest'].sum()],
        'change_OI': [df['changeinOpenInterest'].sum()],
        'pct_change_OI' : [((df['changeinOpenInterest'].sum() / df['openInterest'].sum()) * 100).round(2) ],
        'CE_OI': [ce_df['openInterest'].sum()],
        'CE_change_OI': [ce_df['changeinOpenInterest'].sum()],
        'pct_CE_change_OI' : [((ce_df['changeinOpenInterest'].sum() / ce_df['openInterest'].sum()) * 100).round(2) ],
        'PE_OI': [pe_df['openInterest'].sum()],
        'PE_change_OI': [pe_df['changeinOpenInterest'].sum()],
        'pct_PE_change_OI' : [((pe_df['changeinOpenInterest'].sum() / pe_df['openInterest'].sum()) * 100).round(2) ],
        'tradeVolume': [df['totalTradedVolume'].sum()],
        'CE_tradedVolume': [ce_df['totalTradedVolume'].sum()],
        'PE_tradedVolume': [pe_df['totalTradedVolume'].sum()],
        'CE_maxoiStrike' : [ce_df.loc[ce_df['openInterest'].idxmax(), 'strikePrice']],
        'PE_maxoiStrike' : [pe_df.loc[pe_df['openInterest'].idxmax(), 'strikePrice']],
        'atmPCR': [(df[(df['count'].isin(range(-2,3))) & (df['type'] == 'CE')]['openInterest'].sum()/df[(df['count'].isin(range(-2,3))) & (df['type'] == 'PE')]['openInterest'].sum()).round(2)],
        'Max_PCR' : [(pe_df.loc[pe_df['openInterest'].idxmax(), 'openInterest'] / ce_df.loc[ce_df['openInterest'].idxmax(), 'openInterest']).round(2) ],
        'PCR' : [(pe_df['openInterest'].sum() / ce_df['openInterest'].sum()).round(2)],
        'Max_pain': [max_pain],
        'CE_vega': [ce_df['Vega'].sum().round(2)],
        'PE_vega': [pe_df['Vega'].sum().round(2)],
        'CE_theta': [ce_df['Theta'].sum().round(2)],
        'PE_theta': [pe_df['Theta'].sum().round(2)],
        'CE_delta': [ce_df['Delta'].sum().round(2)],
        'PE_delta': [pe_df['Delta'].sum().round(2)]
        
        })

    return greek_df


def calculate_max_pain(df):
    
    # Separate call options and put options
    calls = df[df['type'] == 'CE']
    puts = df[df['type'] == 'PE']

    # Group call options and put options by strike price and calculate total open interest
    call_open_interest = calls.groupby('strikePrice')['openInterest'].sum()
    put_open_interest = puts.groupby('strikePrice')['openInterest'].sum()

    # Combine call and put open interest into a single dataframe
    max_pain_df = pd.DataFrame({'Call OI': call_open_interest, 'Put OI': put_open_interest})

    # Calculate the total open interest as the sum of call and put open interest
    max_pain_df['Total OI'] = max_pain_df['Call OI'] + max_pain_df['Put OI']

    # Exclude rows with NaN values
    max_pain_df = max_pain_df.dropna()

    # Find the strike price with the lowest total open interest
    max_pain_strike = max_pain_df['Total OI'].idxmin()
    
    return max_pain_strike
