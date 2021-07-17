import time

import schedule
from flask import Flask

from apis.constants import fetch_data
from extensions import register_extensions
from models.option_chain import OptionChain
from views import register_base_routes
from views import register_json_routes


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
app = Flask(__name__, instance_relative_config=False)
register_extensions(app)
register_json_routes(app)
register_base_routes(app)
# return app


# app = create_webapp()

if __name__ == "__main__":
    # Start application
    app.run()
