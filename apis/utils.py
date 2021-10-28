from datetime import datetime

import requests

from apis.constants import strategy_id_name_dct, strategy_symbol_dict
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

        if option_data["atm"]:
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
        data["entry_price"] = constructed_data[f'{strike}_{data["option_type"]}']
    elif strike_price:
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
        if data["symbol"] in ["BANKNIFTY", "NIFTY"] or data.get("atm"):
            strike = constructed_data["atm"]
            data["strike"] = int(float(strike))
            data["entry_price"] = constructed_data[
                f'{strike.split(".")[0]}_{data["option_type"]}'
            ]
        else:
            # TODO not completed yet, need to decide which one to buy atm or with most vol
            options_data_lst = fetch_data(data["symbol"])
            max_vol = 0
            max_vol_strike = None
            max_vol_strike_price = None
            for option_data in options_data_lst:
                option_vol = float(option_data[f'{data["option_type"]}Qt']["vol"])
                if option_vol > max_vol:
                    max_vol = option_vol
                    max_vol_strike = option_data["stkPrc"]
                    max_vol_strike_price = option_data[f'{data["option_type"]}Qt'][
                        "ltp"
                    ]

            data["strike"] = int(float(max_vol_strike))
            data["entry_price"] = max_vol_strike_price

    if data.get("future_price"):
        del data["future_price"]

    if data.get("action"):
        data["quantity"] = (
            data["quantity"] if data["action"] == "buy" else -data["quantity"]
        )
        del data["action"]

    if data.get("atm"):
        del data["atm"]

    data["placed_at"] = current_time

    obj = self.create_object(data, kwargs={})
    return last_trades, obj


def get_computed_profit(strategy_id=None):
    if strategy_id:
        constructed_data = get_constructed_data(
            symbol=strategy_symbol_dict[int(strategy_id)]
        )
    else:
        bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
        nifty_constructed_data = get_constructed_data(symbol="NIFTY")
        axis_bank_constructed_data = get_constructed_data(symbol="AXISBANK")
        bajaj_finance_constructed_data = get_constructed_data(symbol="BAJFINANCE")
        tata_motors_constructed_data = get_constructed_data(symbol="TATAMOTORS")
        sbi_constructed_data = get_constructed_data(symbol="SBIN")
        adanient_constructed_data = get_constructed_data(symbol="ADANIENT")

    data = []

    total_profits = 0
    total_completed_profits = 0
    total_ongoing_profits = 0
    for _strategy_id in (
        [strategy_id]
        if strategy_id
        else (NFO.query.with_entities(NFO.strategy_id).distinct(NFO.strategy_id).all())
    ):
        ongoing_profit, completed_profit, completed_trades, ongoing_trades = 0, 0, 0, 0

        for nfo in NFO.query.filter_by(strategy_id=_strategy_id).all():
            if strategy_id:
                constructed_data = constructed_data
            elif nfo.symbol == "BANKNIFTY":
                constructed_data = bank_nifty_constructed_data
            elif nfo.symbol == "NIFTY":
                constructed_data = nifty_constructed_data
            elif nfo.symbol == "AXISBANK":
                constructed_data = axis_bank_constructed_data
            elif nfo.symbol == "TATAMOTORS":
                constructed_data = tata_motors_constructed_data
            elif nfo.symbol == "BAJFINANCE":
                constructed_data = bajaj_finance_constructed_data
            elif nfo.symbol == "SBIN":
                constructed_data = sbi_constructed_data
            elif nfo.symbol == "ADANIENT":
                constructed_data = adanient_constructed_data

            if nfo.exited_at:
                completed_profit += nfo.profit
                completed_trades += 1
            else:
                ongoing_profit += get_profit(
                    nfo,
                    float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),
                )

                ongoing_trades += 1

        total_strategy_profits = completed_profit + ongoing_profit
        total_profits += total_strategy_profits
        total_completed_profits += completed_profit
        total_ongoing_profits += ongoing_profit
        data.append(
            {
                "id": _strategy_id[0],
                "name": strategy_id_name_dct[int(_strategy_id[0])],
                "completed": {
                    "trades": completed_trades,
                    "profit": round(completed_profit, 2),
                },
                "on_going": {
                    "trades": ongoing_trades,
                    "profit": round(ongoing_profit, 2),
                },
                "total": {
                    "trades": ongoing_trades + completed_trades,
                    "profit": round(total_strategy_profits, 2),
                },
            }
        )

    result = {
        "data": data,
        "meta": {
            "total_profits": round(total_profits, 2),
            "total_completed_profits": round(total_completed_profits, 2),
            "total_ongoing_profits": round(total_ongoing_profits, 2),
        },
    }
    return result


def close_all_trades(strategy_id):
    bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
    nifty_constructed_data = get_constructed_data(symbol="NIFTY")

    update_mappings = []
    exited_at = datetime.now()

    for strategy_id in (
        [strategy_id]
        if strategy_id
        else (NFO.query.with_entities(NFO.strategy_id).distinct(NFO.strategy_id).all())
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
            update_mapping = {"id": nfo.id, "profit": profit, "exited_at": exited_at}
            update_mappings.append(update_mapping)

    db.session.bulk_update_mappings(NFO, update_mappings)
    db.session.commit()

    return "All trades closed successfully"


def fetch_data(symbol="BANKNIFTY", expiry="03 NOV 2021"):
    if symbol in ["BANKNIFTY", "NIFTY"]:
        atyp = "OPTIDX"
        expiry = expiry
    else:
        atyp = "OPTSTK"
        expiry = "28 OCT 2021"

    return requests.post(
        "https://ewmw.edelweiss.in/api/Market/optionchaindetails",
        data={"exp": expiry, "aTyp": atyp, "uSym": symbol},
    ).json()["opChn"]


# wpp martin suarel
#
# vivek bharghava
# dentsu
