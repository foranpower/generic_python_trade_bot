import configparser
import datetime as dt
import sys
import os
import pandas as pd

config = configparser.ConfigParser()


try:
    config.read(r"config.ini")
    DIR = config["SETTINGS"]["DIR"]
except:
    config.read(r"../config.ini")
    DIR = config["SETTINGS"]["DIR"]

mode = config["SETTINGS"]["mode"].lower()
iv_symbols = config["SETTINGS"]["iv_symbols"].split(',')
tokens_file = config['SETTINGS']['tokens_file']

lookback = int(config['TRADEDETAILS']['lookback'])
period = 1 if config['TRADEDETAILS']['period'] == 'day' else 7
past_days = period * lookback
minutes_to_wait_at_open = int(config['TRADEDETAILS']['minutes_to_wait_at_open'])
seconds_between_tries = int(config['TRADEDETAILS']['seconds_between_tries'])

cause_start = config['TRADEDETAILS']['cause_start']
cause_end = config['TRADEDETAILS']['cause_end']
effect_start = config['TRADEDETAILS']['effect_start']
effect_end = config['TRADEDETAILS']['effect_end']

effect_end = int(config['TRADEDETAILS']['entry_start_execution_duration'])
effect_end = int(config['TRADEDETAILS']['exit_end_execution_duration'])

df_tokens = pd.read_csv(tokens_file, header=None).set_index(0)

token = df_tokens.loc['Token', 1] if mode == 'brokerage' else df_tokens.loc['Sandbox_Token', 1]
account_id = df_tokens.loc['AccountId', 1] if mode == 'brokerage' else df_tokens.loc['Sandbox_AccountId', 1]

api_string = 'api' if mode == 'brokerage' else 'sandbox'

import time
import urllib.parse
from typing import Optional, Dict, Any, List
import datetime as dt

import numpy as np
from scipy import stats
from requests import Request, Session, Response
import hmac
import logging

inputs = pd.read_csv(os.path.join(DIR,'data','trade_config.csv'))
