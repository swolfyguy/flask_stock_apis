import datetime

from dateutil import parser
import matplotlib.pyplot as plt
import csv

from apis.utils import (
    get_computed_profit,
    get_computed_profit_without_fetching_completed_profit,
    fetch_data,
    get_constructed_data,
)
from extensions import db
from main import app
from models.completed_profit import CompletedProfit
from models.nfo import NFO
from models.till_yesterdays_profit import TillYesterdaysProfit


def generate_csv():
    file = "db_data/31_jan.csv"
    with open(file, "w") as csvfile:
        outcsv = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        header = NFO.__table__.columns.keys()
        outcsv.writerow(header)

        for record in NFO.query.filter(NFO.exited_at != None).order_by(NFO.id).all():
            outcsv.writerow([getattr(record, c) for c in header])


# with app.app_context():
#     generate_csv()


if __name__ != "__main__":
    ## uncomment if you want to download db data to csv
    # with app.app_context():
    #     generate_csv()

    x = []
    y = []

    # for row in pd.read_csv('nfo_new.csv', nrows=1000):
    #     pass

    date_profit_dict = {}
    with open("db_data/24_jan.csv", "r") as csvfile:
        lines = csv.reader(csvfile, delimiter=",")
        for index, row in enumerate(lines):
            # strategy_id
            if row[10] == "5":
                try:
                    exited_at_date_time = parser.parse(row[7])
                    date_ = exited_at_date_time.date()
                    if date_ in date_profit_dict:
                        date_profit_dict[date_] = date_profit_dict[date_] + int(
                            eval(row[5])
                        )
                    else:
                        date_profit_dict[date_] = int(eval(row[5]))
                except:
                    pass

    sum = 0
    for key, value in date_profit_dict.items():
        x.append(key)
        sum = sum + value
        y.append(sum)

    plt.plot(x, y, color="g", linestyle="-", marker="o", label="profit")

    # joins the x and y values
    for x, y in zip(x, y):
        label = round(y / 100000, 2)

        plt.annotate(
            label,  # this is the value which we want to label (text)
            (x, y),  # x and y is the points location where we have to label
            textcoords="offset points",
            xytext=(0, 10),  # this for the distance between the points
            # and the text label
            ha="left",
            arrowprops=dict(arrowstyle="->", color="green"),
        )

    plt.xticks(rotation=25)
    plt.xlabel("date_time")
    plt.ylabel("profit")
    plt.title("banknifty", fontsize=20)
    plt.grid()
    plt.legend()
    plt.show()


def add_column():
    with app.app_context():
        col = db.Column("expiry", db.Date)
        column_name = col.compile(dialect=db.engine.dialect)
        column_type = col.type.compile(db.engine.dialect)
        table_name = NFO.__tablename__
        db.engine.execute(
            "ALTER TABLE %s ADD COLUMN %s %s" % (table_name, column_name, column_type)
        )
        db.session.commit()


# add_column()

#
# def delete_rows():
#     with app.app_context():
#         delete_q = NFO.__table__.delete().where(
#             NFO.placed_at <= datetime.datetime(2022, 2, 3, 7, 30)
#         )
#         db.session.execute(delete_q)
#         db.session.commit()
#
#
# delete_rows()


def undo_last_action():
    with app.app_context():
        delete_q = NFO.__table__.update().where(
            NFO.exited_at >= datetime.datetime(2022, 1, 13, 16, 0, 0)
        )
        db.session.execute(delete_q)
        db.session.commit()


def take_next_expiry_trades():
    last_action = dict(
        [
            (3, -25),
            (2, 100),
            (4, 100),
            (5, 25),
            (6, 100),
            (7, 25),
            (8, 25),
            (9, 100),
            (10, 100),
            (11, 100),
            (26, 25),
            (100, -25),
            (101, 100),
            (1, -25),
        ]
    )

    ongoing_trades = {
        100: 75,
        4: 31,
        11: 1,
        10: 11,
        6: 1,
        101: 17,
        1: 1,
        3: 4,
        8: 2,
        2: 1,
        7: 2,
        9: 2,
        5: 1,
        26: 2,
    }
    with app.app_context():
        bank_nifty_constructed_data = get_constructed_data(symbol="BANKNIFTY")
        nifty_constructed_data = get_constructed_data(symbol="NIFTY")

        for strategy_id in ongoing_trades:
            nfo = NFO.query.filter_by(strategy_id=strategy_id).first()
            if nfo.symbol == "BANKNIFTY":
                strike_price = 500
                constructed_data = bank_nifty_constructed_data
            else:
                strike_price = 200
                constructed_data = nifty_constructed_data

            option_type = "ce" if last_action[strategy_id] > 0 else "pe"
            entry_price, strike = 0, 0
            for key, value in constructed_data.items():
                if (
                    option_type in key
                    and -50 < (float(value) - float(strike_price)) < 100
                ):
                    entry_price, strike = value, key.split("_")[0]
                    break

            placed_at = datetime.datetime.now()
            new_nfo = NFO(
                entry_price=entry_price,
                strike=strike,
                placed_at=placed_at,
                quantity=ongoing_trades[strategy_id] * 25
                if nfo.symbol == "BANKNIFTY"
                else 50,
                nfo_type="option",
                option_type=option_type,
                strategy_id=strategy_id,
                strategy_name=nfo.strategy_name,
                symbol=nfo.symbol,
            )
            db.session.add(new_nfo)

        db.session.commit()


def difference_call():
    with app.app_context():
        action = "buy"
        for nfo in (
            NFO.query.filter(
                NFO.strategy_id == 11, NFO.placed_at >= datetime.datetime(2022, 1, 13)
            )
            .order_by(NFO.placed_at)
            .all()
        ):
            on_going_action = "buy" if nfo.quantity > 0 else "sell"
            if action != on_going_action:
                print(
                    on_going_action,
                    nfo.placed_at + datetime.timedelta(hours=5, minutes=30),
                )
                action = on_going_action


# difference_call()


def compare_db_with_tdview_profit():
    csv_lookup = {}
    with open("trading_view_chart_calls/banknifty_single_call_28.csv", "r") as csvfile:
        lines = csv.reader(csvfile, delimiter=",")
        for index, row in enumerate(lines):
            if index > 0:
                if row[0] not in csv_lookup:
                    csv_lookup[row[0]] = [row[3], row[6]]
                else:
                    if row[3] != "":
                        csv_lookup[row[0]].append(row[3])
                    else:
                        del csv_lookup[row[0]]

    datetime_format = "%Y-%m-%d %H:%M"
    final_csv_lookup = {
        datetime.datetime.strptime(value[0], datetime_format): (
            datetime.datetime.strptime(value[2], datetime_format),
            value[1],
        )
        for key, value in csv_lookup.items()
    }

    # print(final_csv_lookup)

    profit = []
    unrealized_profit = 0
    with app.app_context():
        for nfo in (
            NFO.query.filter(
                NFO.strategy_id == 5,
                NFO.placed_at >= datetime.datetime(2022, 1, 4),
                NFO.exited_at != None,
            )
            .order_by(NFO.placed_at)
            .all()
        ):
            hour = nfo.placed_at.hour
            minute = nfo.placed_at.minute
            iso_placed_at_datetime = nfo.placed_at.replace(
                second=0, microsecond=0, tzinfo=None
            )
            iso_exited_at_datetime = nfo.exited_at.replace(
                second=0, microsecond=0, tzinfo=None
            )

            ist_placed_at_datetime = iso_placed_at_datetime + datetime.timedelta(
                hours=5, minutes=30
            )
            ist_exited_at_datetime = iso_exited_at_datetime + datetime.timedelta(
                hours=5, minutes=30
            )

            if ist_placed_at_datetime in final_csv_lookup:
                if ist_placed_at_datetime.weekday() != 4:

                    _profit = float(final_csv_lookup[ist_placed_at_datetime][1]) - (
                        nfo.profit
                    )
                    if (
                        final_csv_lookup[ist_placed_at_datetime][0]
                        == ist_exited_at_datetime
                    ):
                        profit.append(_profit)
                    else:
                        unrealized_profit += _profit

        profit.sort()
        # print(f"final profit: {profit}")
        print(f"unrealized_profit profit: {unrealized_profit}")


# compare_db_with_tdview_profit()

# take_next_expiry_trades()

# RIGHT ON SPOT with tradingview in terms of call
# BankNifty Every Candle 87,
# Nifty Every Candle 21

# BankNifty Affordable 27 , one candle behind  Strategy_id = 7
# BankNifty Testing Affordable 14 , sometimes one candle sometimes its 3 candles behind   Strategy_id = 8
# BankNifty Single Call 28, Right on spot only one candle behind
# BankNifty 41 is also on spot
# BankNifty 26 is also on spot, it skips one pair of buy and sell sometimes


# Nifty Single Call 3 and 21 results are different.... TODO check for 21 again after 14 Jan
# Nifty Affordable 9, one candle behind strategy_id=9
# Nifty Testing Affordable 3, RESULTS DO NOT MATCH TradingView
# Nifty 18 is RIGHT ON SPOT


#
#
# def update_completed_profit():
#     with app.app_context():
#         response = get_computed_profit_without_fetching_completed_profit()
#
#         for strategy_profit in response["data"]:
#             strategy_id = strategy_profit["id"]
#             df = CompletedProfit(
#                 strategy_id=strategy_id,
#                 profit=strategy_profit["completed"]["profit"],
#                 trades=strategy_profit["completed"]["trades"],
#             )
#             db.session.add(df)
#             print(f"going to update completed profit: {strategy_id}")
#         try:
#             db.session.commit()
#         except Exception as e:
#             print(f"Error occurred while updating CompletedProfit profit: {e}")
#             db.session.rollback()
