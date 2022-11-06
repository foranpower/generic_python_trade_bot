import asyncio
from typing import Any, Awaitable

# create a few programs ## here, I'm trying to run trade1, ...2, 3, 4... all in parallel
# not sure how to wake program up at trade start time, or perhaps a little before to collect data, then sleep it after completing it's mission, until trade_exit condition is hit (for now just time such as 10:30am.
wake_up_program = [
    Message(trade1_id, MessageType.GO),
    Message(trade2_id, MessageType.GO),
    Message(trade3_id, MessageType.GO),
    Message(trade456789..._id, MessageType.GO),
]

# run the programs for each specific trade such as trade1 ##somehow need to add a trade1 id to each trade1_id part, trade2_id to each trade 2 part.
await service.run_program(wake_up_program)
await run_parallel(
    run_sequence(
        service.send_msg(Message(data_collector_id, MessageType.GO)),
        service.send_msg(Message(predictor_id, MessageType.GO)),
        service.send_msg(Message(trade_entry_id, MessageType.GO)),
        service.send_msg(Message(trade_exit_id, MessageType.GO)),
        ## perhaps sleeping the program could go here
    ),
)

async def run_sequence(*functions: Awaitable[Any]) -> None:
    for function in functions:
        await function


async def run_parallel(*functions: Awaitable[Any]) -> None:
    await asyncio.gather(*functions)