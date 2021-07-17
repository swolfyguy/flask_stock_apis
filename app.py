import time

import schedule
from flask import Flask

from apis.constants import fetch_data
from extensions import register_extensions
from models.option_chain import OptionChain
from views import register_base_routes
from views import register_json_routes
import logging

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
app = Flask(__name__, instance_relative_config=False)
try:
    register_extensions(app)
    register_json_routes(app)
    register_base_routes(app)
except Exception as e:
    logging.info(f"error while running :{e}")

# return app


# app = create_webapp()

if __name__ == "__main__":
    gunicorn_logger=logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    # Start application
    app.run()
