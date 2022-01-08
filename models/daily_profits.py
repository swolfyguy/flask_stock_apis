# Create data storage
from extensions import db


class DailyProfits(db.Model):
    __tablename__ = "daily_profits"

    id = db.Column(db.Integer, primary_key=True)
    profit = db.Column(db.Float, nullable=True)
    strategy_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)