import json
from datetime import date, datetime

from nsepy.derivatives import get_expiry_date

from apis.constants import fetch_data
from extensions import db
from models.nfo import NFO


def get_profit(trade, ltp):
    if trade.quantity > 0:
        b, a = ltp, trade.entry_price
    else:
        b, a = trade.entry_price, ltp

    return (b - a) * trade.quantity


def buy_or_sell_future(self, data: dict):
    last_trade = NFO.query.filter_by(
        strategy_id=data["strategy_id"], exited_at=None, nfo_type="future"
    ).scalar()

    ltp = data["entry_price"]

    if last_trade:
        last_trade.exit_price = ltp
        last_trade.profit = get_profit(last_trade, ltp)
        last_trade.exited_at = datetime.now()
        db.session.commit()
        db.session.refresh(last_trade)

    data["entry_price"] = ltp
    # just in case we receive strike price as an additional attribute delete it
    if data.get("strike_price"):
        del data["strike_price"]

    if data.get("option_type"):
        del data["option_type"]

    if data.get("strike"):
        del data["strike"]

    obj = self.create_object(data, kwargs={})
    return last_trade, obj


def get_constructed_data(options_data_lst=None):
    if not options_data_lst:
        options_data_lst = get_options_data_list()

    constructed_data = {}
    for option_data in options_data_lst:
        constructed_data.update(
            {
                f'{option_data["strike"]}_ce': option_data["celtp"],
                f'{option_data["strike"]}_pe': option_data["peltp"],
            }
        )
    return constructed_data


def get_options_data_list(symbol="BANKNIFTY"):
    todays_date = date.today()
    current_month_expiry_list = sorted(
        get_expiry_date(year=todays_date.year, month=todays_date.month, index=symbol)
    )
    options_expiry_dt = None
    for dt in current_month_expiry_list:
        if dt > todays_date:
            options_expiry_dt = dt
            break

    formatted_expiry = ""
    if options_expiry_dt:
        formatted_expiry = f"{options_expiry_dt.day}{options_expiry_dt.strftime('%b').upper()}{options_expiry_dt.year}"

    res = fetch_data(symbol, expiry=formatted_expiry)
    return json.loads(res.json()["OptionChainInfo"])


def buy_or_sell_option(self, data: dict):
    # TODO fetch expiry from nse lib
    current_time = datetime.now()
    constructed_data = get_constructed_data(get_options_data_list(data["symbol"]))

    last_trades = NFO.query.filter_by(
        strategy_id=data["strategy_id"], exited_at=None, nfo_type="option"
    ).all()

    data["option_type"] = "ce" if data["action"] == "buy" else "pe"
    if last_trades:
        if last_trades[0].option_type != data["option_type"]:
            mappings = []
            for trade in last_trades:
                exit_price = constructed_data[f"{trade.strike}_{trade.option_type}"]
                mappings.append(
                    {
                        "id": trade.id,
                        "profit": get_profit(trade, exit_price),
                        "exit_price": exit_price,
                        "exited_at": current_time,
                    }
                )

            db.session.bulk_update_mappings(NFO, mappings)
            db.session.commit()

    strike_price = data.get("strike_price")
    strike = data.get("strike")
    if strike:
        # strike_option_data = list(
        #     filter(
        #         lambda option_data: option_data["strike"] == strike, options_data_lst
        #     )
        # )[0]
        # data["entry_price"] = strike_option_data[f"{data['option_type']}ltp"]
        data["entry_price"] = constructed_data[f'{strike}_{data["option_type"]}']
    elif strike_price:
        # strike_option_data = list(
        #     filter(
        #         lambda option_data: -50
        #         < (
        #             int(option_data[f"{data['option_type']}ltp"])
        #             if isinstance(option_data[f"{data['option_type']}ltp"], float)
        #             else 0
        #         )
        #         - int(strike_price)
        #         < 100,
        #         options_data_lst,
        #     )
        # )[0]
        entry_price, strike = 0, 0
        for key, value in constructed_data.items():
            if (
                -50
                < (
                    (
                        int(value)
                        if data["option_type"] in key and isinstance(value, float)
                        else 0
                    )
                    - int(strike_price)
                )
                < 100
            ):
                entry_price, strike = value, key.split("_")[0]
                break
        data["entry_price"] = entry_price
        data["strike"] = strike
        # strike_price doesnt make entry to database its only for selection of exact strike price which is entry price
        del data["strike_price"]
    else:
        # strike_option_data = list(
        #     filter(
        #         lambda option_data: option_data[f"{data['option_type']}status"]
        #         == "ATM",
        #         options_data_lst,
        #     )
        # )[0]
        strike = int(round(float(data["future_price"]) / 100) * 100)
        data["strike"] = strike
        data["entry_price"] = constructed_data[f'{strike}_{data["option_type"]}']

    if data.get("future_price"):
        del data["future_price"]

    if data.get("action"):
        del data["action"]

    obj = self.create_object(data, kwargs={})
    return last_trades, obj


def get_computed_profit(nfo_list=None):
    constructed_data = get_constructed_data()
    profit = 0
    for nfo in NFO.query.all() if not nfo_list else nfo_list:
        if nfo.profit:
            profit += nfo.profit
        else:
            profit = profit + get_profit(
                nfo, constructed_data[f"{nfo.strike}_{nfo.option_type}"]
            )
    return str(round(profit, 2))
