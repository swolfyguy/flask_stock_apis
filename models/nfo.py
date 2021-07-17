# Create data storage
from datetime import datetime

from extensions import db


class NFO(db.Model):
    __tablename__ = "nfo"

    id = db.Column(db.Integer, primary_key=True)
    nfo_type = db.Column(db.String, nullable=False)

    # order detail
    action = db.Column(db.String, nullable=False, server_default="buy")
    quantity = db.Column(db.Integer, default=25)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=True)
    profit = db.Column(db.Float, nullable=True)

    # option specific field
    strike = db.Column(db.Integer, nullable=True)
    option_type = db.Column(db.String, nullable=True)

    # future specific field
    future_price = db.Column(db.Float, nullable=True)

    # strategy details
    strategy = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String, nullable=False)

    # execution details
    placed_at = db.Column(
        db.TIMESTAMP(timezone=True), nullable=False, default=datetime.now()
    )
    exited_at = db.Column(db.TIMESTAMP(timezone=True), nullable=True)
