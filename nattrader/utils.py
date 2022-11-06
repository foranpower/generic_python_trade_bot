import pandas as pd
import yfinance as yf
import numpy as np
import math
from nattrader.get_data_from_tradier import get_latest_quote
from nattrader import *


def convert_into_prediction(df, past_days):
    pchanges = df.pct_change()
    pchanges = pchanges[-1 * past_days:]

    if pchanges.iloc[-1] < 0:
        # ochanges = pchanges[pchanges<0]
        diffs = pchanges.iloc[-1] - pchanges[pchanges < 0].iloc[:-1]
    elif pchanges.iloc[-1] > 0:
        # ochanges = pchanges[pchanges>0]
        diffs = pchanges.iloc[-1] - pchanges[pchanges > 0].iloc[:-1]
    else:
        # ochanges = pchanges[pchanges==0]
        diffs = pchanges.iloc[-1] - pchanges[pchanges == 0].iloc[:-1]

    abs_diffs = diffs.abs()
    return pchanges.iloc[pchanges.index.get_loc(abs_diffs.idxmin()) + 1]


def return_to_prediction(rets, ticker, token, period):
    '''
    Calculate prediction based on closeness of today's return vs all days in lookback.
    For the closest day in history, the next day's return becomes the prediction for current day

    Args:
        rets (): past returns
        ticker (): target ticker
        token ():
        period ():

    Returns:

    '''
    # Get recent close for ticker
    last_price = get_latest_quote(ticker, token)

    # Calc Close to Open for all dates
    # rets['ao'].iloc[-1] = last_price
    # rets['c_o'].iloc[-1] = rets['ao'].iloc[-1] / rets['bc'].iloc[-1] - 1

    # Apply the grid
    last_co = rets['cause_ret'].iloc[-1]
    if last_co < 0:
        diffs = rets[rets < 0]['cause_ret'] - rets['cause_ret'].iloc[-1]
    elif last_co > 0:
        diffs = rets[rets > 0]['cause_ret'] - rets['cause_ret'].iloc[-1]
    else:
        diffs = rets[rets == 0]['cause_ret'] - rets['cause_ret'].iloc[-1]

    abs_diffs = diffs.abs()
    if period == 7:
        weekday = abs_diffs.index[-1].weekday()
        abs_diffs = abs_diffs[abs_diffs.index.weekday == weekday]

    min_idx = abs_diffs[:-1].idxmin()
    if not type(min_idx) == float:
        return rets.loc[min_idx, 'effect_ret'], last_price
    else:
        return 0, last_price

def calc_returns_new(minute_data,
     cause_start_time, cause_start_days,
     cause_end_time, cause_end_days,
     effect_start_time, effect_start_days,
     effect_end_time, effect_end_days,
     period, lookback):

    # cause_start_time = dt.datetime.strptime(cause_start_time, '%H:%M').time()
    # cause_end_time = dt.datetime.strptime(cause_end_time, '%H:%M').time()
    # effect_start_time = dt.datetime.strptime(effect_start_time, '%H:%M').time()
    # effect_end_time = dt.datetime.strptime(effect_end_time, '%H:%M').time()

    targets = pd.DataFrame(
        columns=[
            'cause_start', 'cause_end', 'effect_start', 'effect_end'
        ])

    unique_dates = list(np.unique(minute_data.index.date)[::-1])
    target_days = []
    for i in range(0, lookback*period, period):
        target_days.append(unique_dates[i])


    for today in target_days:

        cs_day = unique_dates[unique_dates.index(today) + cause_start_days]
        ce_day = unique_dates[unique_dates.index(today) + cause_end_days]
        es_day = unique_dates[unique_dates.index(today) - effect_start_days]
        ee_day = unique_dates[unique_dates.index(today) - effect_end_days]

        # cause_start = dt.datetime.combine(cs_day,cause_start_time)
        # cause_end = dt.datetime.combine(ce_day, cause_end_time)
        # effect_start = dt.datetime.combine(es_day, effect_start_time)
        # effect_end = dt.datetime.combine(ee_day, effect_end_time)

        cause_start = cs_day.strftime('%Y-%m-%d') + ' ' + cause_start_time
        cause_end = ce_day.strftime('%Y-%m-%d') + ' ' + cause_end_time
        effect_start = es_day.strftime('%Y-%m-%d') + ' ' + effect_start_time
        effect_end = ee_day.strftime('%Y-%m-%d') + ' ' + effect_end_time

        cs_price = minute_data[:cause_start]['Close'].iloc[-1]
        ce_price = minute_data[:cause_end]['Close'].iloc[-1]
        es_price = minute_data[:effect_start]['Close'].iloc[-1]
        ee_price = minute_data[:effect_end]['Close'].iloc[-1]

        targets.loc[today] = [cs_price, ce_price, es_price, ee_price]

    targets = targets.dropna()
    targets.index = pd.to_datetime(targets.index)
    # targets['bc'] = targets['bc'].shift(1)
    targets['cause_ret'] = targets['cause_end'] / targets['cause_start'] - 1
    targets['effect_ret'] = targets['effect_end'] / targets['effect_start'] - 1

    return targets.iloc[::-1]

def get_prices_from_tradier(ticker, tradier):
    '''
    Retrieves prices from tradier for a single stock
    Args:
        ticker (): target stock symbol
        tradier (): tradier object

    Returns:

    '''
    stocks = tradier.stock(ticker)
    company = tradier.company(symbol=ticker)
    history = company.history(interval='daily', start='2021-09-01')
    closes = pd.Series(history.close())
    return closes

def get_sandbox_token():
    # Version 3.6.1
    import requests

    response = requests.post('https://api.tradier.com/v1/oauth/accesstoken',
                             headers={'Authorization': 'Basic <token>', 'Accept': 'application/json'}
                             )
    json_response = response.json()
    print(response.status_code)
    print(json_response)


if __name__ == '__main__':
    # Sample
    df = pd.Series(
        [100, 109, 98, 102, 103, 98, 99, 100, 110, 112, 105, 107]
    )
    convert_into_prediction(df, 9)

    # aapl_df = yf.download('AAPL',
    #                       start='2021-12-12',
    #                       end='2021-12-19',
    #                       interval='1m'
    #                       )
    # aapl_df.head()
