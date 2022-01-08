# Create data storage
from extensions import db


class CompletedProfit(db.Model):
    __tablename__ = "completed_profit"

    id = db.Column(db.Integer, primary_key=True)
    profit = db.Column(db.Float, nullable=True)
    strategy_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.Date, nullable=False, default=db.func.now())
    updated_at = db.Column(db.Date, nullable=True)
