# generic_python_trade_bot


### This project was made by:
   #Forest Kirschbaum
   #Abhishek Gupta - Amazing programmer
   #Dale - Great at asycio
   #rleonard's PyTradier is used to interface with Tradier. https://github.com/rleonard21/PyTradier



### Project Setup
1. Set the parameters as per the description in following section.
2. Create two environment variables:
    * 'NAT_token': Token for your trading account
    * 'NAT_accountid': Account ID of the trading account
  

### Parameters Description
DIR: Set to the directory where this readme is placed in your system
mode: brokerage or sandbox
iv_symbols: to download data for
period = daily, weekly, monthly
lookback = days to go back for looking cause event


### Run Modes
1. Parameter 'mode' can take 3 values:
    - brokerage: For Live Account
    - brokerage_sandbox: For Full API functionality for paper trading
    - developer_sandbox: For Limited API functionality for paper trading

### TODO
  Weekly Cycle
  End to End Test of Code
    try to get an entry for 15 minutes, then give up.
    exit: start trying to get an exit 60 minutes after open, keep trying for 90 minutes.
    execution
    refresh to stay in sync with the market to get our fill.


​
