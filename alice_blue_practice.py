import datetime
from datetime import date
from time import sleep

from alice_blue import AliceBlue, LiveFeedType

app_id = 'FgshPEm3jw'
secret = '9wg5GZzBhiOjVrf10OGYjwECrMVSnwecSLRtp8hsvJwyWDiGpFpTzOvTkwypJOcs'

alice = AliceBlue(
    "569619",
    "SANkok@94",
    "sJaR69XLRoRYifX4HegNWjB-4_snDQqJg-8VsUVtJdg.dqpvE7BnLgAys8myMjUFtYp5wt95ktQ1BS6H-V1lpEQ",
)


socket_opened = False

start_time = datetime.datetime.now()


def event_handler_quote_update(message):
    print(f'time taken to update: {datetime.datetime.now() - start_time}')
    print(f"quote update {message['ltp']}")


def open_callback():
    global socket_opened
    socket_opened = True


alice.start_websocket(
    subscribe_callback=event_handler_quote_update,
    socket_open_callback=open_callback,
    run_in_background=True,
)


instrument = alice.get_instrument_for_fno(
    symbol="BANKNIFTY",
    expiry_date=date(2022, 3, 31),
    is_fut=True,
    strike=None,
    is_CE=False,
)

while True:
    alice.subscribe(instrument, LiveFeedType.MARKET_DATA)
    # sleep(10)
