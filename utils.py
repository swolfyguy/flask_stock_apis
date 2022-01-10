from dateutil import parser
import matplotlib.pyplot as plt
import csv

from apis.utils import get_computed_profit, get_computed_profit_without_fetching_completed_profit
from extensions import db
from main import app
from models.completed_profit import CompletedProfit
from models.nfo import NFO
from models.till_yesterdays_profit import TillYesterdaysProfit


def generate_csv():
    file = "db_data/14_dec.csv"
    with open(file, "w") as csvfile:
        outcsv = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        header = NFO.__table__.columns.keys()
        outcsv.writerow(header)

        for record in NFO.query.order_by(NFO.id).all():
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
    with open("nfo_new_2.csv", "r") as csvfile:
        lines = csv.reader(csvfile, delimiter=",")
        for index, row in enumerate(lines):
            if row[10] == "6":
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


def delete_rows():
    with app.app_context():
        delete_q = NFO.__table__.delete().where(NFO.exited_at != None)
        db.session.execute(delete_q)
        db.session.commit()


def update_profit():
    with app.app_context():
        update_ = (
            NFO.__table__.update()
            .where(NFO.exited_at != None)
            .values(profit=NFO.profit - 30)
        )
        db.session.execute(update_)
        db.session.commit()


def add_column():
    with app.app_context():
        col = db.Column('trades', db.Integer)
        column_name = col.compile(dialect=db.engine.dialect)
        column_type = col.type.compile(db.engine.dialect)
        table_name = CompletedProfit.__tablename__
        db.engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))
        db.session.commit()


def update_completed_profit():
    with app.app_context():
        response = get_computed_profit_without_fetching_completed_profit()

        for strategy_profit in response["data"]:
            strategy_id = strategy_profit["id"]
            df = CompletedProfit(
                strategy_id=strategy_id,
                profit=strategy_profit["completed"]["profit"],
                trades=strategy_profit["completed"]["trades"]
            )
            db.session.add(df)
            print(f"going to update completed profit: {strategy_id}")
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error occurred while updating CompletedProfit profit: {e}")
            db.session.rollback()

update_completed_profit()