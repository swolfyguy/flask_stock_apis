# Create data storage
import datetime
from datetime import date

from extensions import db


class OptionChain(db.Model):
    __tablename__ = "option_chain"

    id = db.Column(db.Integer, primary_key=True)

    strike = db.Column(db.Integer, nullable=False, default=10000)

    celtp = db.Column(db.Float, nullable=True, default=0.0)
    celtt = db.Column(db.Time, nullable=True, default=datetime.datetime.now().time())

    peltp = db.Column(db.Float, nullable=True, default=0.0)
    peltt = db.Column(db.Time, nullable=True, default=datetime.datetime.now().time())

    date = db.Column(db.Date, default=date.today())
