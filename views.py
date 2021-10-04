# Create endpoints
import datetime
import time

import schedule
from flask import jsonify
from flask_rest_jsonapi import Api

from apis.nfo import NFODetail
from apis.nfo import NFOList
from apis.option_chain import OptionChainList, OptionChainDetail
from apis.utils import get_computed_profit, get_constructed_data
from models.option_chain import OptionChain
from extensions import db


def update_option_chain(symbol="BANKNIFTY"):
    print(f"dumping option chain at: {datetime.datetime.now().time()}")
    constructed_data = get_constructed_data(symbol=symbol)

    option_chain_db_stkprc_list = [
        r[0]
        for r in OptionChain.query.with_entities(OptionChain.strike, OptionChain.id)
        .filter(OptionChain.symbol == symbol)
        .all()
    ]

    update_mappings = []
    for strike, id in option_chain_db_stkprc_list:

        if f"{strike}_pe" in constructed_data:
            data_to_update = {
                "id": id,
                "peltp": constructed_data[f"{strike}_pe"],
                "celtp": constructed_data[f"{strike}_ce"],
            }

            if strike == constructed_data["atm"]:
                data_to_update.update({"atm": True})
            update_mappings.append(data_to_update)

    db.session.bulk_update_mappings(OptionChain, update_mappings)

    # if insert_mappings:
    #     db.session.bulk_insert_mappings(OptionChain, insert_mappings)

    db.session.commit()


def register_base_routes(app):
    @app.route("/")
    def index():
        response = "Hello from a public endpoint! You don't need to be authenticated to see this."
        return jsonify(message=response)

    @app.route("/api/schedule/dump_option_chain")
    def dump_option_chain():
        schedule.every(15).seconds.do(update_option_chain)
        while True:
            schedule.run_pending()
            time.sleep(1)

    @app.route("/api/profit")
    def compute_profit():
        return get_computed_profit()


def register_json_routes(app):
    api = Api(app)

    # Expected Payload
    {
        "data": {
            "type": "option",
            "attributes": {
                "strategy": 1,  # mandatory
                "nfo_type": "option",  # mandatory for now
                "option_type": "ce",
                "action": "buy",  # mandatory
                "strike_price": 550,  # if not provided ATM strike price will be picked
                "symbol": "BANKNIFTY",  # its optional,
            },
        }
    }

    api.route(NFOList, "nfo_list", "/api/nfo")
    api.route(NFODetail, "nfo_detail", "/api/nfo/<int:id>")

    api.route(OptionChainList, "option_chain_list", "/api/option_chain")
    api.route(OptionChainDetail, "option_chain_detail", "/api/nfo/<int:id>")
