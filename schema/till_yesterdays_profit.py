# Create logical data abstraction (same as data storage for this first example)
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema


class TillYesterdaysProfitSchema(Schema):
    class Meta:
        type_ = "till_yestardays_profit"
        self_view = "till_yestardays_profit_detail"
        self_view_kwargs = {"id": "<id>"}
        self_view_many = "till_yestardays_profit_list"

    id = fields.Integer(as_string=True, dump_only=True)
    profit = fields.Float()
    strategy_id = fields.Integer()
