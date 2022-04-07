import datetime

from alice_blue import AliceBlue, TransactionType, OrderType, ProductType

from extensions import db
from models.broker import Broker


def place_alice_blue_order(
    strike_quantity_dict, symbol, expiry: datetime.date, nfo_type, action
):
    """
    assumptions
     all trades to be executed should belong to same:
      symbol [ for ex: either BANKNIFTY, NIFTY ]
      expiry
      call type [ for ex: either CE, PE ]
      nfo type [ for ex: either future or option]
    """

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

        order_id = alice.place_order(
            transaction_type=TransactionType.Buy
            if action == "buy"
            else TransactionType.Sell,
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
        close_order_action_id_list.append(order_id)

    for _id in close_order_action_id_list:
        response = alice.get_order_history(_id)
        if response["status"] == "success":
            continue
        else:
            print(response)
