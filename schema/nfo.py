# Create logical data abstraction (same as data storage for this first example)
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema


class NFOSchema(Schema):
    class Meta:
        type_ = "nfo"
        self_view = "nfo_detail"
        self_view_kwargs = {"id": "<id>"}
        self_view_many = "nfo_list"

    id = fields.Integer(as_string=True, dump_only=True)
    nfo_type = fields.String()

    # order detail
    action = fields.String()
    quantity = fields.Integer()
    entry_price = fields.Float()
    exit_price = fields.Float()
    profit = fields.Float()

    # option specific field
    strike = fields.Integer()
    option_type = fields.String()

    # future specific
    future_price = fields.Float(load_only=True)

    # strategy details
    strategy = fields.Integer()

    # execution timings
    placed_at = fields.DateTime()
    exited_at = fields.DateTime()

    # Temporary fields which doesnt have existence in db
    symbol = fields.String()  # TODO move it to models later
    strike_price = fields.Float(load_only=True)
