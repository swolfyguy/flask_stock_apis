# Create resource managers
import json
import logging
from copy import deepcopy
from datetime import datetime

from flask import request
from flask_rest_jsonapi import ResourceDetail
from flask_rest_jsonapi import ResourceList
from flask_rest_jsonapi.decorators import check_method_requirements
from flask_rest_jsonapi.exceptions import ObjectNotFound
from flask_rest_jsonapi.schema import compute_schema
from marshmallow import ValidationError
from marshmallow_jsonapi.exceptions import IncorrectTypeError
from sqlalchemy.orm.exc import NoResultFound
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager

from apis.constants import fetch_data
from extensions import db
from models.nfo import NFO
from schema.nfo import NFOSchema

log = logging.getLogger(__file__)


class NFODetail(ResourceDetail):
    # ignore below code its dummy
    def before_get_object(self, view_kwargs):
        if view_kwargs.get("computer_id") is not None:
            try:
                computer = (
                    self.session.query(NFO)
                    .filter_by(id=view_kwargs["computer_id"])
                    .one()
                )
            except NoResultFound:
                raise ObjectNotFound(
                    {"parameter": "computer_id"},
                    "Computer: {} not found".format(view_kwargs["computer_id"]),
                )
            else:
                if computer.person is not None:
                    view_kwargs["id"] = computer.person.id
                else:
                    view_kwargs["id"] = None

    schema = NFOSchema
    data_layer = {
        "session": db.session,
        "model": NFO,
        "methods": {"before_get_object": before_get_object},
    }


def get_profit(trade, ltp):
    if trade.quantity > 0:
        b, a = ltp, trade.entry_price
    else:
        b, a = trade.entry_price, ltp

    return (b - a) * 25


def buy_or_sell_future(self, data: dict):
    last_trade = NFO.query.filter_by(
        strategy_id=data["strategy_id"], exited_at=None, nfo_type="future"
    ).scalar()

    ltp = data["entry_price"]

    if last_trade:
        last_trade.exit_price = ltp
        last_trade.profit = get_profit(last_trade, ltp)
        last_trade.exited_at = datetime.now()
        db.session.commit()
        db.session.refresh(last_trade)

    data["entry_price"] = ltp
    # just in case we receive strike price as an additional attribute delete it
    if data.get("strike_price"):
        del data["strike_price"]

    if data.get("option_type"):
        del data["option_type"]

    if data.get("strike"):
        del data["strike"]

    obj = self.create_object(data, kwargs={})
    return last_trade, obj


def buy_or_sell_option(self, data: dict):
    # TODO fetch expiry from nse lib
    res = fetch_data(data["symbol"])
    options_data_lst = json.loads(res.json()["OptionChainInfo"])

    last_trade = NFO.query.filter_by(
        strategy_id=data["strategy_id"], exited_at=None, nfo_type="option"
    ).scalar()

    if last_trade:
        old_strike_option_data = list(
            filter(
                lambda option_data: option_data["strike"] == last_trade.strike,
                options_data_lst,
            )
        )[0]
        ltp = old_strike_option_data[f"{last_trade.option_type}ltp"]
        last_trade.exit_price = ltp
        last_trade.profit = get_profit(last_trade, ltp)
        last_trade.exited_at = datetime.now()

        db.session.commit()
        db.session.refresh(last_trade)

    strike_price = data.get("strike_price")
    strike = data.get("strike")
    if strike:
        strike_option_data = list(
            filter(
                lambda option_data: option_data["strike"] == strike, options_data_lst
            )
        )[0]
    elif strike_price:
        strike_option_data = list(
            filter(
                lambda option_data: -50
                < (
                    int(option_data[f"{data['option_type']}ltp"])
                    if isinstance(option_data[f"{data['option_type']}ltp"], float)
                    else 0
                )
                - int(strike_price)
                < 100,
                options_data_lst,
            )
        )[0]
        data["strike"] = strike_option_data["strike"]
        # strike_price doesnt make entry to database its only for selection of exact strike price which is entry price
        del data["strike_price"]
    else:
        strike_option_data = list(
            filter(
                lambda option_data: option_data[f"{data['option_type']}status"]
                == "ATM",
                options_data_lst,
            )
        )[0]
        data["strike"] = strike_option_data["strike"]

    data["entry_price"] = strike_option_data[f"{data['option_type']}ltp"]
    obj = self.create_object(data, kwargs={})
    return last_trade, obj


class NFOList(ResourceList):
    @check_method_requirements
    def post(self, *args, **kwargs):
        """Create an object"""
        json_data = request.get_json() or {}

        qs = QSManager(request.args, self.schema)

        schema_kwargs = getattr(self, "post_schema_kwargs", dict())
        schema = compute_schema(
            self.schema, schema_kwargs, qs, qs.include
        )

        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as e:
            errors = e.messages
            for error in errors["errors"]:
                error["status"] = "409"
                error["title"] = "Incorrect type"
            return errors, 409
        except ValidationError as e:
            errors = e.messages
            for message in errors["errors"]:
                message["status"] = "422"
                message["title"] = "Validation error"
            return errors, 422

        if errors:
            for error in errors["errors"]:
                error["status"] = "422"
                error["title"] = "Validation error"
            return errors, 422

        if data.get("nfo_type").lower() == "future":
            objects = buy_or_sell_future(self, data)
        elif data.get("nfo_type").lower() == "option":
            objects = buy_or_sell_option(self, data)
        else:
            object_1 = buy_or_sell_future(self, data)
            object_2 = buy_or_sell_option(self, data)
            objects = [*object_1, *object_2]

        schema_kwargs.update({'many': True})
        schema = compute_schema(
            self.schema, schema_kwargs, qs, qs.include
        )
        result = schema.dump(objects).data
        return result

    schema = NFOSchema
    data_layer = {
        "session": db.session,
        "model": NFO,
    }
