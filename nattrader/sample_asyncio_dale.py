import asyncio

from nattrader import *

async def wait_until(dte):
    # sleep until the specified datetime
    now = dt.datetime.now()
    await asyncio.sleep((dte - now).total_seconds())

async def run_at(dt, coro):
    await wait_until(dt)
    return await coro

async def enter_trade(symbol):
    print(f'Waiting to enter trade at {dt.datetime.now()}')
    await asyncio.sleep(120)
    print(f'Entered Trade for {symbol} at {dt.datetime.now()}')


async def exit_trade(symbol):
    print(f'Waiting to exit trade at {dt.datetime.now()}')
    await asyncio.sleep(120)
    print(f'Exited Trade for {symbol} at {dt.datetime.now()}')


if __name__ == '__main__':

    inputs = pd.read_csv(DIR + r'/data/sample_dale.csv')

    inputs.Time = pd.to_datetime(inputs.Time)

    inputs['Delay'] = (inputs.Time - dt.datetime.now()).apply(lambda x: x.total_seconds() / 60)

    loop = asyncio.get_event_loop()
    for i, row in inputs.iterrows():
        if row['Type'] == 'Enter':
            loop.create_task(run_at(row['Time'],enter_trade(row['Asset'])))
        else:
            loop.create_task(run_at(row['Time'],exit_trade(row['Asset'])))

    print('Waiting for the trades')
    loop.run_forever()

