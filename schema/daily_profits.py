# Create logical data abstraction (same as data storage for this first example)
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema


class DailyProfitsSchema(Schema):
    class Meta:
        type_ = "daily_profits"
        self_view = "daily_profits_detail"
        self_view_kwargs = {"id": "<id>"}
        self_view_many = "daily_profits_list"

    id = fields.Integer(as_string=True, dump_only=True)
    profit = fields.Float()
    strategy_id = fields.Integer()
