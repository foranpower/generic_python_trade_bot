import datetime as dt

import pandas as pd
from polygon import RESTClient
# from nattrader.utils import calc_returns


def ts_to_datetime(ts) -> str:
    return dt.datetime.utcfromtimestamp(ts / 1000.0).strftime('%Y-%m-%d %H:%M')

df_tokens = pd.read_csv('/home/guest144/bumblebee/data/Tokens.csv', index_col="data_provider")

def dl_polygon_single(ticker, from_='2021-01-01', to='2021-01-10', ndays=False):
    key = str(df_tokens.loc['polygonio_key','token_value'])

    if ndays:
        to = dt.datetime.now().date()
        from_ = to - dt.timedelta(ndays*1.5)

    # RESTClient can be used as a context manager to facilitate closing the underlying http session
    # https://requests.readthedocs.io/en/master/user/advanced/#session-objects
    with RESTClient(key) as client:
        resp = client.stocks_equities_aggregates(ticker, 1, "minute", from_, to, unadjusted=False, limit=50000)

        print(f"Minute aggregates for {resp.ticker} between {from_} and {to}.")

        df = pd.DataFrame(resp.results)
        df.rename(columns={
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume',
            't': 'time'
        }, inplace=True)

        df = df[['time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df['time'] = df['time'].apply(ts_to_datetime)
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York')

        return df


def dl_polygon(tickers, from_='2021-01-01', to='2021-01-10'):
    prices = {}
    for ticker in tickers:
        prices[ticker] = dl_polygon_single(ticker, from_, to)
    return prices


if __name__ == '__main__':
    minute_data = dl_polygon_single('AAPL')
    # df_returns = calc_returns(minute_data)
