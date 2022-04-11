import datetime

from alice_blue import AliceBlue, TransactionType, OrderType, ProductType

from extensions import db
from models.broker import Broker


def get_alice_blue_obj():
    broker = Broker.query.filter_by(name="alice_blue").scalar()
    try:
        alice = AliceBlue(
            username=broker.username,
            password=broker.password,
            access_token=broker.access_token,
            master_contracts_to_download=["NFO"],
        )
    except:
        broker = Broker.query.filter_by(name="alice_blue").with_for_update().scalar()
        access_token = AliceBlue.login_and_get_access_token(
            username=broker.username,
            password=broker.password,
            twoFA="1994",
            api_secret=broker.api_secret,
            app_id=broker.app_id,
        )
        broker.access_token = access_token
        db.session.commit()

        alice = AliceBlue(
            username=broker.username,
            password=broker.password,
            access_token=access_token,
            master_contracts_to_download=["NFO"],
        )

    return alice


def close_alice_blue_trades(
    strike_quantity_dict, symbol, expiry: datetime.date, nfo_type
):
    """
    assumptions
     all trades to be executed should belong to same:
      symbol [ for ex: either BANKNIFTY, NIFTY ]
      expiry
      call type [ for ex: either CE, PE ]
      nfo type [ for ex: either future or option]
    """

    alice = get_alice_blue_obj()
    close_order_action_id_list = []

    if isinstance(expiry, str):
        expiry = datetime.datetime.strptime(expiry, "%d %b %Y").date()

    for strike, quantity in strike_quantity_dict.items():
        instrument = alice.get_instrument_for_fno(
            symbol=symbol,
            expiry_date=expiry,
            is_fut=nfo_type != "option",
            strike=strike,
            is_CE=quantity > 0,
        )

        place_order_response = alice.place_order(
            transaction_type=TransactionType.Sell,
            instrument=instrument,
            quantity=quantity if quantity > 0 else (-1 * quantity),
            order_type=OrderType.Market,
            product_type=ProductType.Delivery,
            price=0.0,
            trigger_price=None,
            stop_loss=None,
            square_off=None,
            trailing_sl=None,
            is_amo=False,
        )
        close_order_action_id_list.append(place_order_response["data"]["oms_order_id"])

    # check for this
    # for order_id in close_order_action_id_list:
    #     response = alice.get_order_history(order_id)
    #     if response["status"] == "success":
    #         continue
    #     else:
    #         print(response)


def buy_alice_blue_trades(
    strike_quantity_dict, symbol, expiry: datetime.date, nfo_type
):
    """
    assumptions
     all trades to be executed should belong to same:
      symbol [ for ex: either BANKNIFTY, NIFTY ]
      expiry
      call type [ for ex: either CE, PE ]
      nfo type [ for ex: either future or option]
    """

    alice = get_alice_blue_obj()
    buy_order_action_id_list = []

    if isinstance(expiry, str):
        expiry = datetime.datetime.strptime(expiry, "%d %b %Y").date()

    for strike, quantity in strike_quantity_dict.items():
        instrument = alice.get_instrument_for_fno(
            symbol=symbol,
            expiry_date=expiry,
            is_fut=nfo_type != "option",
            strike=strike,
            is_CE=quantity > 0,
        )

        place_order_response = alice.place_order(
            transaction_type=TransactionType.Buy,
            instrument=instrument,
            quantity=quantity if quantity > 0 else (-1 * quantity),
            order_type=OrderType.Market,
            product_type=ProductType.Delivery,
            price=0.0,
            trigger_price=None,
            stop_loss=None,
            square_off=None,
            trailing_sl=None,
            is_amo=False,
        )
        buy_order_action_id_list.append(place_order_response["data"]["oms_order_id"])

    for order_id in buy_order_action_id_list:
        return (
            "success"
            if alice.get_order_history(order_id)["data"][0]["order_status"] == "complete"
            else "error"
        )
