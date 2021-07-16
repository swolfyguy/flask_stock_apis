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


class NFOList(ResourceList):
    @check_method_requirements
    def post(self, *args, **kwargs):
        """Create an object"""
        json_data = request.get_json() or {}

        qs = QSManager(request.args, self.schema)

        schema = compute_schema(self.schema,
                                getattr(self, 'post_schema_kwargs', dict()),
                                qs,
                                qs.include)

        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as e:
            errors = e.messages
            for error in errors['errors']:
                error['status'] = '409'
                error['title'] = "Incorrect type"
            return errors, 409
        except ValidationError as e:
            errors = e.messages
            for message in errors['errors']:
                message['status'] = '422'
                message['title'] = "Validation error"
            return errors, 422

        if errors:
            for error in errors['errors']:
                error['status'] = "422"
                error['title'] = "Validation error"
            return errors, 422

        self.before_post(args, kwargs, data=data)

        future_data = deepcopy(data)
        # delete option specific data
        del future_data["strike"]
        # del future_data["option_type"]
        future_data["nfo_type"] = "future"
        future_data["entry_price"] = future_data["future_price"]
        if future_data.get("strike_price"):
            del future_data["strike_price"]

        # delete future specific data
        del data["future_price"]
        if data["action"] == "buy":
            data["option_type"] = "ce"
        else:
            data["option_type"] = "pe"
        data["nfo_type"] = "option"
        if data.get("strike_price"):
            del data["strike_price"]

        option_obj = self.create_object(data, kwargs)
        future_obj = self.create_object(future_data, kwargs)

        result = schema.dump(option_obj).data

        if result['data'].get('links', {}).get('self'):
            final_result = (result, 201, {'Location': result['data']['links']['self']})
        else:
            final_result = (result, 201)

        result = self.after_post(final_result)

        return result

    def before_post(self, args, kwargs, data=None):
        # TODO create two object one for future another for option
        if data["nfo_type"] == "option":
            last_trade_list = NFO.query.filter_by(
                strategy=data["strategy"], exited_at=None
            ).all()
            # TODO fetch expiry from nse lib
            res = fetch_data(data["symbol"])
            data_lst = json.loads(res.json()["OptionChainInfo"])
            strike_price = data.get("strike_price")
            strike = data.get("strike")
            if not data.get("option_type"):
                option_type = "ce" if data["action"] == "buy" else "pe"
            else:
                option_type = data["option_type"]

            option_last_trade = False
            future_last_trade = False
            if last_trade_list:
                for last_trade in last_trade_list:
                    if last_trade.nfo_type == "option":
                        option_last_trade = last_trade
                    if last_trade.nfo_type == "future":
                        future_last_trade = last_trade

            if strike:
                for option_data in data_lst:
                    if option_data["strike"] == strike:
                        data["entry_price"] = option_data[f"{option_type}ltp"]
                        break
                    if (
                        option_last_trade
                        and option_data["strike"] == option_last_trade.strike
                    ):
                        exit_price = option_data[f"{option_last_trade.option_type}ltp"]
            elif strike_price:
                exit_price_found = False if option_last_trade else True
                entry_price_found = False

                for option_data in data_lst:
                    if isinstance(option_data[f"{option_type}ltp"], float):
                        ltp = int(option_data[f"{option_type}ltp"])
                    else:
                        ltp = 0

                    diff = ltp - int(data["strike_price"])
                    if not entry_price_found and -50 < diff < 100:
                        data["entry_price"] = ltp
                        data["strike"] = option_data["strike"]
                        entry_price_found = True
                    if option_last_trade and option_data["strike"] == option_last_trade.strike:
                        exit_price = option_data[f"{option_last_trade.option_type}ltp"]
                        exit_price_found = True

                    if exit_price_found and entry_price_found:
                        del data["strike_price"]
                        break
            else:
                for option_data in data_lst:
                    if option_data[f"{option_type}status"] == "ATM":
                        data["entry_price"] = option_data[f"{option_type}ltp"]
                        data["strike"] = option_data["strike"]
                        break
                    if (
                        option_last_trade
                        and option_data["strike"] == option_last_trade.strike
                    ):
                        exit_price = option_data[f"{option_last_trade.option_type}ltp"]

            if option_last_trade:
                option_last_trade.profit = (
                    exit_price - option_last_trade.entry_price
                ) * 25
                option_last_trade.exit_price = exit_price
                option_last_trade.exited_at = datetime.now()
                db.session.add(option_last_trade)

            if future_last_trade:
                future_ltp = data["future_price"]
                future_last_trade.exit_price = future_ltp
                diff = (future_ltp - future_last_trade.entry_price) * 25
                future_last_trade.profit = (
                    diff if future_last_trade.action == "buy" else -diff
                )
                future_last_trade.exited_at = datetime.now()
                db.session.add(future_last_trade)

            db.session.commit()

        # do not remove below code
        # if data["option_type"] == "PE":
        #     pass
        # else:
        #     last_trade_list = Option.query.order_by(Option.created_at.desc()).all()
        #     if last_trade_list:
        #         option_last_trade = last_trade_list[0]
        #         exit_price = nsepython.nse_quote_ltp(
        #             "BANKNIFTY", "24-Jun-2021", "PE", 34500
        #         )
        #         option_last_trade.exit_price = exit_price
        #         option_last_trade.profit = exit_price - option_last_trade.entry_price
        #         option_last_trade.updated_at = datetime.now()
        #         db.session.add(option_last_trade)
        #         db.session.commit()
        #
        #     data["entry_price"] = nsepython.nse_quote_ltp(
        #         "BANKNIFTY", "24-Jun-2021", "CE", 34500
        #     )

    schema = NFOSchema
    data_layer = {
        "session": db.session,
        "model": NFO,
    }
