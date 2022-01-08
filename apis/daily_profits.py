# Create resource managers
from flask_rest_jsonapi import ResourceDetail, ResourceList

from extensions import db
from models.daily_profits import DailyProfits
from schema.daily_profits import DailyProfitsSchema


class DailyProfitsList(ResourceList):
    methods = ["GET"]
    schema = DailyProfitsSchema
    data_layer = {"session": db.session, "model": DailyProfits}


class DailyProfitsDetail(ResourceDetail):
    schema = DailyProfitsSchema
    methods = ["GET"]
    data_layer = {"session": db.session, "model": DailyProfits}
