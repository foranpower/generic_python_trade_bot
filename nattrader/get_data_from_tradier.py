import traceback
import pandas as pd
import re
from nattrader.calc_iv import implied_vol
from nattrader import *
import requests
import datetime as dt


def get_closes(ticker, tradier):
    company = tradier.company(symbol=ticker)
    history = company.history(interval='daily', start='2021-09-01')
    opt_closes = pd.Series(history.close()).rename('Price').dropna()
    return opt_closes


def get_historical_iv(tradier, opt, ndays, chain, options, closes):
    try:
        opt_closes = get_closes(opt, tradier)
        opt_closes = opt_closes[~pd.to_numeric(opt_closes, errors='coerce').isnull()]
        df = pd.DataFrame(opt_closes)
        closes.rename('Underlying', inplace=True)
        df = df.join(closes)
        df.index = pd.to_datetime(df.index)
        df['strikes'] = options['strikes'].loc[opt]
        df['rfrate'] = 0.032
        df['exp'] = (df.index - pd.to_datetime(chain._expiration)).days
        df['exp'] = df['exp'].abs() / 365
        df['q'] = 0.01
        df['direction'] = 'c' if re.search('\w\d+C', opt) else 'p'

        iv = df.apply(lambda x: implied_vol(x['direction'], x['Price'] \
                                            , x['Underlying'], x['strikes'], \
                                            x['rfrate'], x['exp'], x['q']), axis=1)
    except Exception as e:
        # logging.exception(e)
        # traceback.print_exc()

        return 0

    return iv[-1 * ndays:]


def send_request(api, token, params={}):
    response = requests.get(f'https://{api_string}.tradier.com/v1//' + api,
                            params=params,
                            headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
                            )
    try:
        if response.status_code == 200:
            json_response = response.json()
        else:
            print(f'Error due to {response.status_code}')
            print(f'Reason: {response.text}')
            json_response = response.text
    except ValueError as e:
        print(f'Error due to parsing response. Content: {response.content}')
        traceback.print_exc()
        return 'Error'
    return json_response


def get_positions(token, account_id):
    api = f'accounts/{account_id}/positions'
    json_response = send_request(api, token)
    return json_response


def get_latest_quote(ticker, token):
    api = f'markets/quotes'
    params = {'symbols': ticker}
    json_response = send_request(api, token, params)
    return json_response['quotes']['quote']['last']


def get_option_df(tradier, ticker, current_close, delay=21):
    itr_date = dt.datetime.now() + dt.timedelta(delay)

    for _ in range(60):
        if itr_date.weekday() == 4:
            date_str = itr_date.strftime('%Y-%m-%d')
            chain = tradier.company(ticker).chain(date_str)
            if len(chain.symbol()) == 0:
                print(f'No option for date {date_str} for ticker {ticker}')
            else:
                chain = tradier.company(ticker).chain(date_str, greeks=True)
                options = pd.DataFrame(chain.greeks()).T
                strikes = chain.strike()
                options['strikes'] = pd.Series(strikes)
                options['diff_strike'] = options['strikes'] - current_close
                options['abs_diff_strike'] = options['diff_strike'].abs()
                options.sort_values('abs_diff_strike', inplace=True)

                options = options.iloc[:4]
                return options, chain

        itr_date = itr_date + dt.timedelta(1)
    return 0


def get_order_info(account_id, order_id):
    api = f'accounts/{account_id}/orders/{order_id}'
    json_response = send_request(api, token)
    return json_response


def modify_order(account_id, order_id, price):
    api = f'accounts/{account_id}/orders/{order_id}'
    json_response = send_request(api, token, params={'price': price})
    return json_response


def is_market_open():
    api = f'markets/clock'
    json_response = send_request(api, token)
    return json_response['clock']['state']


if __name__ == '__main__':
    pass
