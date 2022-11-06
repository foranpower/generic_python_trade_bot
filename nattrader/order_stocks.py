import sys

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import requests
import re
from nattrader import *
from nattrader.PyTradier.pytradier.tradier import Tradier
from nattrader.get_data_from_tradier import send_request, get_order_info


def trade_stock():

    response = requests.post(f'https://{api_string}.tradier.com/v1/accounts/{account_id}/orders',
                             data={'class': 'equity', 'symbol': 'AAPL', 'side': 'buy', 'quantity': '10',
                                   'type': 'limit', 'duration': 'day', 'price': '1.00', 'stop': '1.00', 'tag': 'my-tag-example-1'},
                             headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
                             )
    if response.status_code == 200:
        json_response = response.json()
        print(json_response)
    else:
        print(f'Error due to {response.status_code}')
        print(f'Reason: {response.text}')
    return json_response



if __name__ == '__main__':
    today = dt.datetime.now().date()

    # Parameters
    ticker = iv_symbols[0]
    # tradier = Tradier(token=token, account_id=account_id, endpoint='brokerage_sandbox')
    tradier = Tradier(token=token, endpoint='developer_sandbox')

    # minute_data = dl_polygon_single(ticker, ndays=past_days)
    res = trade_stock()
    order_id = res['order']['id']
    order_id = 13856201
    info = get_order_info(account_id, order_id)['order']

    # data = {'q': 'sbin.ns', 'exchanges': 'C', 'types': 'stock'}
    # res = send_request('markets/lookup', token, params=data)

