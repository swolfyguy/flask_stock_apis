# Create endpoints
import datetime
import json
import time

import schedule
from flask import app
from flask import jsonify
from flask_rest_jsonapi import Api

from apis.nfo import NFODetail
from apis.nfo import NFOList
from apis.constants import fetch_data
from apis.option_chain import OptionChainList, OptionChainDetail
from apis.utils import get_computed_profit
from models.nfo import NFO
from models.option_chain import OptionChain
from extensions import db


def update_option_chain():
    print(f"dumping option chain at: {datetime.datetime.now().time()}")
    res = fetch_data(symbol="BANKNIFTY")
    binary_data_lst = res.json()["OptionChainInfo"]

    valid_columns = OptionChain.__table__.c.keys()
    valid_columns.remove("date")
    option_chain_db_id_list = [
        r[0] for r in OptionChain.query.with_entities(OptionChain.id).all()
    ]

    update_mappings = []
    insert_mappings = []
    data_lst = json.loads(binary_data_lst)
    for option_chain_data in data_lst:
        if int(option_chain_data["id"]) in option_chain_db_id_list:
            update_mappings.append(
                {
                    column: option_chain_data[column]
                    if option_chain_data[column]
                    else None
                    for column in option_chain_data
                    if column in valid_columns
                }
            )
        else:
            insert_mappings.append(
                {
                    column: option_chain_data[column]
                    if option_chain_data[column]
                    else None
                    for column in option_chain_data
                    if column in valid_columns
                }
            )

    db.session.bulk_update_mappings(OptionChain, update_mappings)

    if insert_mappings:
        db.session.bulk_insert_mappings(OptionChain, insert_mappings)

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
