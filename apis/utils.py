import copy
from datetime import datetime

import requests
import sqlalchemy

from sqlalchemy.util._collections import _LW

from apis.constants import TRADES
from extensions import db
from models.completed_profit import CompletedProfit
from models.nfo import NFO


EXPIRY_LISTS = [
    "03 FEB 2022",
    "10 FEB 2022",
    "17 FEB 2022",
    "24 FEB 2022",
    "03 MAR 2022",
    "10 MAR 2022",
    "17 MAR 2022",
    "24 MAR 2022",
    "31 MAR 2022",
    "28 APR 2022",
]


def get_current_expiry():
    expiry = None
    today_date = datetime.today().date()
    for expiry_str in EXPIRY_LISTS:
        expiry_date = datetime.strptime(expiry_str, "%d %b %Y").date()
        if today_date <= expiry_date:
            return expiry_str
    return expiry


def get_profit(trade, ltp):
    if trade.quantity > 0:
        b, a = ltp, trade.entry_price
    else:
        b, a = trade.entry_price, ltp

    # TODO charges to be deducted should be dynamic because in future apart from Bank and Nifty we will have others F&O
    return (b - a) * trade.quantity - 30


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


def get_constructed_data(symbol="BANKNIFTY", expiry=None):
    options_data_lst = fetch_data(symbol, expiry)

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


def get_final_data(data, expiry, current_time):
    constructed_data = dict(
        sorted(
            get_constructed_data(data["symbol"], expiry=expiry).items(),
            key=lambda item: float(item[1]),
        )
    )

    data["option_type"] = "ce" if data["action"] == "buy" else "pe"
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
    data["expiry"] = expiry

    return data


def buy_or_sell_option(self, data: dict):
    # TODO fetch expiry from nse lib .
    current_time = datetime.now()

    todays_date = datetime.today().date()
    todays_expiry = False
    for index, expiry_str in enumerate(EXPIRY_LISTS):
        expiry_date = datetime.strptime(expiry_str, "%d %b %Y").date()
        if todays_date > expiry_date:
            continue
        elif expiry_date == todays_date:
            next_expiry = EXPIRY_LISTS[index + 1]
            current_expiry = expiry_str
            todays_expiry = True
            break
        elif todays_date < expiry_date:
            current_expiry = EXPIRY_LISTS[index - 1]
            break

    if todays_expiry:
        models = []
        on_going_trades = NFO.query.filter_by(
            strategy_id=data["strategy_id"],
            exited_at=None,
            nfo_type="option",
            symbol=data["symbol"],
            expiry=current_expiry,
        ).all()

        data["option_type"] = "ce" if data["action"] == "buy" else "pe"
        if on_going_trades:
            constructed_data = dict(
                sorted(
                    get_constructed_data(data["symbol"], expiry=current_expiry).items(),
                    key=lambda item: float(item[1]),
                )
            )

            total_ongoing_trades = len(on_going_trades)
            mappings = []
            total_profit = 0
            for trade in on_going_trades:
                exit_price = constructed_data[f"{trade.strike}_{trade.option_type}"]
                profit = get_profit(trade, exit_price)
                mappings.append(
                    {
                        "id": trade.id,
                        "profit": profit,
                        "exit_price": exit_price,
                        "exited_at": current_time,
                        "expiry": current_expiry,
                    }
                )
                total_profit += profit

            cp = CompletedProfit.query.filter_by(strategy_id=trade.strategy_id).scalar()
            if cp:
                cp.profit += total_profit
                cp.trades += len(on_going_trades)
            else:
                cp = CompletedProfit(
                    profit=total_profit,
                    strategy_id=data["strategy_id"],
                    trades=len(on_going_trades),
                )
                db.session.add(cp)

            db.session.bulk_update_mappings(NFO, mappings)
            db.session.commit()

            data_copy = copy.deepcopy(data)
            data_copy["quantity"] = (
                total_ongoing_trades
                * (25 if data_copy["symbol"] == TRADES.BANKNIFTY else 100)
                * (1 if data_copy["action"] == "buy" else -1)
            )
            new_data = get_final_data(
                data=data_copy, expiry=next_expiry, current_time=current_time
            )
            obj = self.create_object(new_data, kwargs={})
            models.append(obj)

        data = get_final_data(
            data=data, expiry=next_expiry, current_time=current_time
        )
        obj = self.create_object(data, kwargs={})
        models.append(obj)

        return models

    constructed_data = dict(
        sorted(
            get_constructed_data(data["symbol"], expiry=current_expiry).items(),
            key=lambda item: float(item[1]),
        )
    )

    on_going_trades = NFO.query.filter_by(
        strategy_id=data["strategy_id"],
        exited_at=None,
        nfo_type="option",
        symbol=data["symbol"],
        expiry=current_expiry,
    ).all()

    if on_going_trades:
        if on_going_trades[0].option_type != data["option_type"]:
            mappings = []
            total_profit = 0
            for trade in on_going_trades:
                exit_price = constructed_data[f"{trade.strike}_{trade.option_type}"]
                profit = get_profit(trade, exit_price)
                mappings.append(
                    {
                        "id": trade.id,
                        "profit": profit,
                        "exit_price": exit_price,
                        "exited_at": current_time,
                    }
                )
                total_profit += profit

            cp = CompletedProfit.query.filter_by(strategy_id=trade.strategy_id).scalar()
            if cp:
                cp.profit += total_profit
                cp.trades += len(on_going_trades)
            else:
                cp = CompletedProfit(
                    profit=total_profit,
                    strategy_id=data["strategy_id"],
                    trades=len(on_going_trades),
                )
                db.session.add(cp)

            db.session.bulk_update_mappings(NFO, mappings)
            db.session.commit()

    data = get_final_data(data, expiry=current_expiry, current_time=current_time)

    obj = self.create_object(data, kwargs={})
    return (obj,)


def get_computed_profit_without_fetching_completed_profit(strategy_id=None):
    if strategy_id:
        constructed_data = get_constructed_data(
            symbol=NFO.query.filter_by(strategy_id=strategy_id).first().symbol,
        )
    else:
        bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
        nifty_constructed_data = get_constructed_data(symbol="NIFTY")
        # axis_bank_constructed_data = get_constructed_data(symbol="AXISBANK")
        # sbi_constructed_data = get_constructed_data(symbol="SBIN")
        # bajajauto_constructed_data = get_constructed_data(symbol="BAJAJ-AUTO")

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

        ongoing_action = None
        for nfo in NFO.query.filter_by(strategy_id=_strategy_id).all():
            if strategy_id:
                constructed_data = constructed_data
            elif nfo.symbol == "BANKNIFTY":
                constructed_data = bank_nifty_constructed_data
            elif nfo.symbol == "NIFTY":
                constructed_data = nifty_constructed_data
            # elif nfo.symbol == "AXISBANK":
            #     constructed_data = axis_bank_constructed_data
            # elif nfo.symbol == "SBIN":
            #     constructed_data = sbi_constructed_data
            # elif nfo.symbol == "BAJAJ-AUTO":
            #     constructed_data = bajajauto_constructed_data
            else:
                continue

            if nfo.exited_at:
                completed_profit += nfo.profit
                completed_trades += 1
            else:
                ongoing_profit += get_profit(
                    nfo,
                    float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),
                )
                ongoing_action = "buy" if nfo.quantity > 0 else "sell"
                ongoing_trades += 1

        total_strategy_profits = completed_profit + ongoing_profit
        total_profits += total_strategy_profits
        total_completed_profits += completed_profit
        total_ongoing_profits += ongoing_profit
        data.append(
            {
                "id": _strategy_id[0],
                "name": nfo.strategy_name,
                "completed": {
                    "trades": completed_trades,
                    "profit": round(completed_profit, 2),
                },
                "on_going": {
                    "trades": ongoing_trades,
                    "profit": round(ongoing_profit, 2),
                    "action": ongoing_action,
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


def get_computed_profit(strategy_id=None):
    if strategy_id:
        constructed_data = get_constructed_data(
            symbol=NFO.query.filter_by(strategy_id=strategy_id).first().symbol,
        )
    else:
        bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
        nifty_constructed_data = get_constructed_data(symbol="NIFTY")
        # axis_bank_constructed_data = get_constructed_data(symbol="AXISBANK")
        # sbi_constructed_data = get_constructed_data(symbol="SBIN")
        # bajajauto_constructed_data = get_constructed_data(symbol="BAJAJ-AUTO")

    data = []

    completed_profit_dict = dict(
        CompletedProfit.query.with_entities(
            CompletedProfit.strategy_id, CompletedProfit
        ).all()
    )
    total_ongoing_profits = 0

    for _strategy_id in (
        [strategy_id]
        if strategy_id
        else (NFO.query.with_entities(NFO.strategy_id).filter_by(exited_at=None).distinct(NFO.strategy_id).all())
    ):
        if isinstance(_strategy_id, _LW):
            _strategy_id = _strategy_id[0]

        ongoing_profit, completed_profit, completed_trades, ongoing_trades = 0, 0, 0, 0

        query = NFO.query.filter_by(exited_at=None, strategy_id=_strategy_id)
        nfo = None
        ongoing_action = None
        for nfo in query.all():
            if strategy_id:
                constructed_data = constructed_data
            elif nfo.symbol == "BANKNIFTY":
                constructed_data = bank_nifty_constructed_data
            elif nfo.symbol == "NIFTY":
                constructed_data = nifty_constructed_data
            else:
                continue

            ongoing_profit += get_profit(
                nfo,
                float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),
            )
            ongoing_action = "buy" if nfo.quantity > 0 else "sell"
            ongoing_trades += 1

        if completed_profit_dict.get(_strategy_id):
            cp_obj = completed_profit_dict[_strategy_id]
            completed_profit = cp_obj.profit
            completed_trades = cp_obj.trades

        total_strategy_profits = ongoing_profit + completed_profit

        total_ongoing_profits += ongoing_profit

        if not nfo:
            nfo = NFO.query.filter_by(strategy_id=_strategy_id).first()

        data.append(
            {
                "id": _strategy_id,
                "name": nfo.strategy_name,
                "completed": {
                    "trades": completed_trades,
                    "profit": completed_profit,
                },
                "on_going": {
                    "trades": ongoing_trades,
                    "profit": round(ongoing_profit, 2),
                    "action": ongoing_action,
                },
                "total": {
                    "trades": ongoing_trades + completed_trades,
                    "profit": round(total_strategy_profits, 2),
                },
            }
        )

    total_completed_profits = sum(
        [cp_obj.profit for cp_obj in completed_profit_dict.values()]
    )
    total_profits = total_completed_profits + total_ongoing_profits
    result = {
        "data": data,
        "meta": {
            "total_profits": round(total_profits, 2),
            "total_completed_profits": round(total_completed_profits, 2),
            "total_ongoing_profits": round(total_ongoing_profits, 2),
        },
    }
    return result


def close_all_trades(strategy_id=None):
    bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
    nifty_constructed_data = get_constructed_data(symbol="NIFTY")
    axis_bank_constructed_data = get_constructed_data(symbol="AXISBANK")
    sbi_constructed_data = get_constructed_data(symbol="SBIN")
    bajajauto_constructed_data = get_constructed_data(symbol="BAJAJ-AUTO")

    update_mappings = []
    exited_at = datetime.now()

    for strategy_id in (
        [strategy_id]
        if strategy_id
        else (NFO.query.with_entities(NFO.strategy_id).distinct(NFO.strategy_id).all())
    ):
        for nfo in NFO.query.filter_by(strategy_id=strategy_id, exited_at=None).all():

            if nfo.symbol == "BANKNIFTY":
                constructed_data = bank_nifty_constructed_data
            elif nfo.symbol == "NIFTY":
                constructed_data = nifty_constructed_data
            # elif nfo.symbol == "AXISBANK":
            #     constructed_data = axis_bank_constructed_data
            # elif nfo.symbol == "SBIN":
            #     constructed_data = sbi_constructed_data
            # elif nfo.symbol == "BAJAJ-AUTO":
            #     constructed_data = bajajauto_constructed_data
            else:
                continue

            ltp = (float(constructed_data[f"{nfo.strike}_{nfo.option_type}"]),)
            profit = get_profit(nfo, ltp)
            update_mapping = {
                "id": nfo.id,
                "profit": profit,
                "exited_at": exited_at,
                "exit_price": ltp,
            }
            update_mappings.append(update_mapping)

    db.session.bulk_update_mappings(NFO, update_mappings)
    db.session.commit()

    return "All trades closed successfully"


def fetch_data(symbol="BANKNIFTY", expiry=None):
    if symbol in ["BANKNIFTY", "NIFTY"]:
        atyp = "OPTIDX"
        if not expiry:
            expiry = get_current_expiry()
    else:
        atyp = "OPTSTK"
        # TODO add logic here as well
        expiry = "24 FEB 2022"

    return requests.post(
        "https://ewmw.edelweiss.in/api/Market/optionchaindetails",
        data={"exp": expiry, "aTyp": atyp, "uSym": symbol},
    ).json()["opChn"]


# wpp martin suarel
#
# vivek bharghava
# dentsu
