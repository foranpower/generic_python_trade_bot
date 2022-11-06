import pandas as pd
from nattrader import *
from nattrader.PyTradier.pytradier.tradier import Tradier
from run_strategy import get_option_chain


df_tokens = pd.read_csv('/home/guest144/bumblebee/data/Tokens.csv', index_col="data_provider")



if __name__ == '__main__':

    past_days = 9
    tradier = Tradier(token=str(df_tokens.loc['Token','token_value']), account_id=str(df_tokens.loc['AccountId','token_value']), endpoint='brokerage')

    history = pd.read_csv(DIR + r'/data/history.csv')
    history.set_index('Unnamed: 0',inplace=True)

    all_dfs = []
    ######### Filter Options ###################
    for ticker in iv_symbols:
        chain = get_option_chain(tradier=tradier, ticker=ticker)
        if chain == 0:
            continue
        options = pd.DataFrame(chain.greeks()).T
        strikes = chain.strike()
        options['strikes'] = pd.Series(strikes)
        all_dfs.append(options)

    today_data = pd.concat(all_dfs)
    today_data['date'] = dt.datetime.now().date()
    today_data = today_data[['date','mid_iv']]

    history.append(today_data).to_csv(DIR + f'/data/history.csv')