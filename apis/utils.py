import json
from datetime import datetime

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


def get_constructed_data(symbol="BANKNIFTY"):
    options_data_lst = fetch_data(symbol)

    constructed_data = {}
    # strikeprice cannot be float for banknifty so remove decimals
    for option_data in options_data_lst:
        strike_price = option_data["stkPrc"][:-2]
        constructed_data.update(
            {
                f"{strike_price}_ce": float(option_data["ceQt"]["ltp"]),
                f"{strike_price}_pe": float(option_data["peQt"]["ltp"]),
            }
        )

        if option_data["atm"] == True:
            constructed_data.update({"atm": option_data["stkPrc"]})

    return constructed_data


def buy_or_sell_option(self, data: dict):
    # TODO fetch expiry from nse lib .
    current_time = datetime.now()
    constructed_data = dict(
        sorted(
            get_constructed_data(data["symbol"]).items(),
            key=lambda item: float(item[1]),
        )
    )

    last_trades = NFO.query.filter_by(
        strategy_id=data["strategy_id"],
        exited_at=None,
        nfo_type="option",
        symbol=data["symbol"],
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
                data["option_type"] in key
                and -50 < (float(value) - float(strike_price)) < 100
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
        # strike = int(round(float(data["future_price"]) / 100) * 100)
        strike = constructed_data["atm"]
        data["strike"] = int(float(strike))
        data["entry_price"] = constructed_data[
            f'{strike.split(".")[0]}_{data["option_type"]}'
        ]

    if data.get("future_price"):
        del data["future_price"]

    if data.get("action"):
        data["quantity"] = (
            data["quantity"] if data["action"] == "buy" else -data["quantity"]
        )
        del data["action"]

    data["placed_at"] = current_time

    obj = self.create_object(data, kwargs={})
    return last_trades, obj


def get_computed_profit():
    bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
    nifty_constructed_data = get_constructed_data(symbol="NIFTY")
    result = {}
    for strategy_id in (
        NFO.query.with_entities(NFO.strategy_id).distinct(NFO.strategy_id).all()
    ):
        ongoing_profit, completed_profit, completed_trades, ongoing_trades = 0, 0, 0, 0
        for nfo in NFO.query.filter_by(strategy_id=strategy_id).all():
            constructed_data = (
                bank_nifty_constructed_data
                if nfo.symbol == "BANKNIFTY"
                else nifty_constructed_data
            )

            if nfo.exited_at:
                completed_profit += nfo.profit
                completed_trades += 1
            else:
                ongoing_profit += get_profit(
                    nfo,
                    float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),
                )
                ongoing_trades += 1

        result.update(
            {
                strategy_id[0]: {
                    "completed": {
                        "trades": completed_trades,
                        "profit": round(completed_profit, 2),
                    },
                    "on-going": {
                        "trades": ongoing_trades,
                        "profit": round(ongoing_profit, 2),
                    },
                    "total": {
                        "trades": ongoing_trades + completed_trades,
                        "profit": round(completed_profit + ongoing_profit, 2),
                    },
                }
            }
        )
    return result


def close_all_trades():
    bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
    nifty_constructed_data = get_constructed_data(symbol="NIFTY")

    update_mappings = []
    exited_at = datetime.now()
    for strategy_id in (
        NFO.query.with_entities(NFO.strategy_id).distinct(NFO.strategy_id).all()
    ):
        for nfo in NFO.query.filter_by(strategy_id=strategy_id, exited_at=None).all():
            constructed_data = (
                bank_nifty_constructed_data
                if nfo.symbol == "BANKNIFTY"
                else nifty_constructed_data
            )
            profit = get_profit(
                    nfo,
                    float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),
                )
            update_mapping = {
                "id": nfo.id,
                "profit": profit,
                "exited_at": exited_at
            }
            update_mappings.append(update_mapping)

    db.session.bulk_update_mappings(NFO, update_mappings)
    db.session.commit()

    return "All trades closed successfully"


# wpp martin suarel
#
# vivek bharghava
# dentsu
