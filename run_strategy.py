import sys
import time

from multiprocessing import Process
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import requests
import re
from nattrader.calc_iv import implied_vol
from nattrader.get_data_from_tradier import *
from nattrader import *
from nattrader.PyTradier.pytradier.tradier import Tradier
from nattrader.utils import convert_into_prediction, return_to_prediction, calc_returns_new
from nattrader.polygon import dl_polygon_single
from nattrader.handler import Handler
import math


def ceil(number, digits) -> float: return math.ceil((10.0 ** digits) * number) / (10.0 ** digits)


class TradierClient:
    _ENDPOINT = 'https://sandbox.tradier.com/v1/' if mode == 'sandbox' else 'https://api.tradier.com/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None, start_date=None, end_date=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name
        self._start_date = start_date
        self._end_date = end_date

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        # self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']


def trade_option(option_symbol, ticker, price=0, preview=True, side='buy_to_open'):
    type = 'market' if price == 0 else 'limit'

    response = requests.post(f'https://{api_string}.tradier.com/v1/accounts/{account_id}/orders',
                             data={'class': 'option', 'symbol': ticker, 'price': price,
                                   'option_symbol': option_symbol, 'side': side, 'quantity': '1',
                                   'type': type, 'duration': 'day', 'preview': preview
                                   },
                             headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
                             )

    global handler
    feedback = handler.check_response(response)

    if not feedback:
        print(f'Error due to {response.status_code}')
        print(f'Reason: {response.text}')
    else:
        print(feedback)
    return feedback


def trade_multileg(oSymbol1, oSymbol2, ticker, price=1.0, preview=True, reverse_side=False):
    '''

    Args:
        oSymbol1 ():
        oSymbol2 ():
        ticker ():
        price ():
        preview ():
        reverse_side (bool): False -> Buy first option and Sell second for opening
                             True -> Sell first option and Buy second for closing

    Returns:

    '''

    side0 = 'buy_to_open' if reverse_side == False else 'sell_to_close'
    side1 = 'sell_to_open' if reverse_side == False else 'buy_to_close'

    response = requests.post(f'https://{api_string}.tradier.com/v1/accounts/{account_id}/orders',
                             data={'class': 'multileg', 'symbol': ticker, 'type': 'market', 'duration': 'day',
                                   'price': price,
                                   'option_symbol[0]': oSymbol1, 'side[0]': side0, 'quantity[0]': '1',
                                   'option_symbol[1]': oSymbol2, 'side[1]': side1, 'quantity[1]': '1',
                                   'preview': preview},
                             headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
                             )
    global handler
    feedback = handler.check_response(response)

    if not feedback:
        print(f'Error due to {response.status_code}')
        print(f'Reason: {response.text}')
    else:
        print(feedback)

    return feedback


def determine_trade(preC, preIV):
    '''
    Determines trade direction based on predictions and Implied volatility

    Args:
        preC ():
        preIV ():

    Returns:

    '''
    if (preC > 0) and (preIV > 0):
        return 'buyCall'
    elif (preC > 0) and (preIV < 0):
        return 'buyVerticalUp'
    elif (preC < 0) and (preIV > 0):
        return 'buyPut'
    elif (preC < 0) and (preIV < 0):
        return 'buyVerticalDown'
    elif (preC == 0) or (preIV == 0):
        return 'exitPosition'


def calc_nat(direction, above, below):
    absym = above._symbols[0]
    besym = below._symbols[0]

    if direction == 'call':
        ask_sell = above.ask()[absym]
        bid_sell = above.bid()[absym]
        ask_buy = below.ask()[besym]
        bid_buy = below.bid()[besym]
    elif direction == 'put':
        ask_sell = below.ask()[besym]
        bid_sell = below.bid()[besym]
        ask_buy = above.ask()[absym]
        bid_buy = above.bid()[absym]

    total_left_unat = bid_buy - ask_sell
    total_right_nat = ask_buy - bid_sell

    midpoint = (total_left_unat + total_right_nat) / 2

    # changed_from: limit_price = abs(midpoint + 0.5 * (total_right_nat - midpoint))
    ###Reason: seems to correctly calculate for debit, credit and even. order type determined below.
    limit_price = (midpoint + 0.1 * (total_right_nat - midpoint))

    # changed_from: return round(limit_price, 2), above_opt, below_opt #simplified to below since we don't need to specify debit/credit/even
    return abs(ceil(limit_price, 2)), absym, besym


def calc_nat_single(opt):
    sym = opt._symbols[0]

    total_left_unat = opt.bid()[sym]
    total_right_nat = opt.ask()[sym]

    midpoint = (total_left_unat + total_right_nat) / 2

    # changed_from: limit_price = abs(midpoint + 0.5 * (total_right_nat - midpoint))
    ###Reason: seems to correctly calculate for debit, credit and even. order type determined below.
    limit_price = (midpoint + 0.1 * (total_right_nat - midpoint))

    # changed_from: return round(limit_price, 2), above_opt, below_opt #simplified to below since we don't need to specify debit/credit/even
    return abs(ceil(limit_price, 2)), sym


def determine_nat(direction, options):
    if direction == 'call':
        sopts = options.filter(regex='\w\d+C', axis=0)
    elif direction == 'put':
        sopts = options.filter(regex='\w\d+P', axis=0)

    sopts = sopts[['strikes']]

    above_opt = sopts.idxmax().loc['strikes']
    below_opt = sopts.idxmin().loc['strikes']

    above = tradier.option(above_opt)
    below = tradier.option(below_opt)

    return calc_nat(direction, above, below)


def send_trades(action, options):
    if action == 'buyVerticalDown':
        nat_price, higher_strike, lower_strike = determine_nat('put', options)
        print(f'{today}-> Put Options choosen for trade are {higher_strike} and {lower_strike}')
        response = trade_multileg(higher_strike, lower_strike, ticker, nat_price)
    elif action == 'buyCall':
        nat_price, higher_strike, lower_strike = determine_nat('call', options)
        print(f'{today}-> Call Option choosen for trade is {lower_strike}')
        response = trade_option(lower_strike, ticker, nat_price)
    elif action == 'buyPut':
        nat_price, higher_strike, lower_strike = determine_nat('put', options)
        print(f'{today}-> Put Option choosen for trade is {higher_strike}')
        response = trade_option(higher_strike, ticker, nat_price)
    elif action == 'buyVerticalUp':
        nat_price, higher_strike, lower_strike = determine_nat('call', options)
        print(f'{today}-> Call Options choosen for trade are {higher_strike} and {lower_strike}')
        response = trade_multileg(higher_strike, lower_strike, ticker, nat_price)
    elif action == 'exitPosition':
        print(f'Since prices are exactly same, lets not enter any trade for today')
        response = 0

    return response


def is_order_filled(order_id):
    info = get_order_info(order_id)
    if info['status'] == 'open':
        return False
    else:
        return True


def try_to_get_fill(func, *args):
    is_filled = False
    minutes_done = False
    start_time = dt.datetime.now()

    response = func(*args)
    if not response:
        while not is_filled or not minutes_done:
            order_info = response['order']
            if order_info.status == 'ok' and ('id' in order_info.keys()):
                order_id = response['id']
                time.sleep(seconds_between_tries)
                is_filled = is_order_filled(order_id)
                spent_seconds = (dt.datetime.now() - start_time).seconds
                minutes_done = spent_seconds > minutes_to_wait_at_open * 60


def trade_ticker(row, run_type):
    # Parameters
    ticker = row['Instrument']
    cause_start = row['cause_start']
    cause_start_days = row['cause_start_days']
    cause_end = row['cause_end']
    cause_end_days = row['cause_end_days']
    effect_start = row['effect_start']
    effect_start_days = row['effect_start_days']
    effect_end = row['effect_end']
    effect_end_days = row['effect_end_days']
    # period = row['period']
    period = 1 if row['period'] == 'day' else 7
    past_days = int(row['lookback'] * period)
    ticker = iv_symbols[0]
    tradier = Tradier(token=token, account_id=account_id, endpoint=mode)

    global handler
    handler = Handler()

    if run_type == 'trading':

        ############### 1. Get Data from Tradier #####################
        minute_data = dl_polygon_single(ticker, ndays=past_days)
        df_returns = calc_returns_new(minute_data,
                                  cause_start, cause_start_days,
                                  cause_end, cause_end_days,
                                  effect_start, effect_start_days,
                                  effect_end, effect_end_days)

        ############### 2. Calculate Cause Event for Closes ##########
        prediction_close, current_close = return_to_prediction(df_returns, ticker, token, period)
        if not prediction_close == 0:
            logging.info(f'{today}-> Prediction for next 1hour return is {prediction_close}')
        else:
            logging.info(f'No valid prediction could be found for next hour. Exiting.')
            sys.exit(0)

        ######### 3. Get Options Data from Tradier ###################
        options, chain = get_option_df(tradier=tradier, ticker=ticker, current_close=current_close)
        today_iv_average = options['mid_iv'].mean()

        hist_ivs = []
        for opt in options.index:
            print(opt)
            hist_ivs.append(get_historical_iv(tradier, opt, past_days, ticker, chain, options))
        df_ivs = pd.concat(hist_ivs, axis=1).mean(axis=1)

        ########### 4. Calculate Cause Event for IV #################
        prediction_iv = convert_into_prediction(df_ivs, past_days)
        print(f'{today}-> Next Day Prediction for IV is {prediction_iv}')

        ########### 5. Determine Effect based on Two Cause Events #####
        action = determine_trade(prediction_close, prediction_iv)
        print(f'{today}-> Action based on predicted close and IV is {action}')

        ########### 6. Based on specified action, calculate nat and send trade ########
        try_to_get_fill(send_trades, action, options)

    else:
        print(f'{today}-> Options to be exited')
        positions = get_positions(token, account_id)
        symbols = []
        if positions['positions'] != 'null':
            for position in positions['positions']['position']:
                symbols.append(position['symbol'])
        else:
            logging.info('No Position present in Portfolio. Exiting now.')
            sys.exit(0)

        if len(symbols) > 1:
            direction = 'call' if 'C' in symbols[0] else 'put'
            first = tradier.option(symbols[0])
            second = tradier.option(symbols[1])

            first_strike = first.strike()[symbols[0]]
            second_strike = second.strike()[symbols[1]]

            above = first if first_strike > second_strike else second
            below = second if first_strike > second_strike else first

            limit_price = calc_nat(direction, above, below)[0]

            try_to_get_fill(trade_multileg,
                            above,
                            below,
                            ticker,
                            limit_price,
                            reverse_side=True
                            )

        else:
            direction = 'call' if 'C' in symbols[0] else 'put'
            invOption = tradier.option(symbols[0])

            limit_price = calc_nat_single(invOption)[0]

            try_to_get_fill(trade_option,
                            invOption,
                            ticker,
                            limit_price,
                            side='sell_to_close'
                            )


if __name__ == '__main__':

    # Run Package only if market is open
    if not is_market_open():
        print(f'Market is closed currently. Please try again once the market opens.')

    today = dt.datetime.now().date()
    parser = argparse.ArgumentParser(description='Enter Mode: 1 for trading, 0 for exit')
    parser.add_argument('-m', metavar='-run_type', type=int,
                        help='an integer for the mode')
    args = parser.parse_args()
    global run_type
    run_type = 'exit' if args.m == 0 else 'trading'

    check_file = Path(DIR + r'\logs\Log_Data' + str(today) + '_' + run_type + '.txt')
    if not check_file.exists() or 1:

        logging.basicConfig(filename=check_file, level=logging.DEBUG, format='%(asctime)s-%(levelname)s-%(message)s')

        processes = []

        for i, row in inputs.iterrows():
            p = Process(target=trade_ticker, args=([row, run_type]))
            p.start()
            processes.append(p)
            break

        for p in processes:
            p.join()
