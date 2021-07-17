import time

import schedule
from flask import Flask

from apis.constants import fetch_data
from extensions import register_extensions
from models.option_chain import OptionChain
from views import register_base_routes
from views import register_json_routes


def _create_app():
    """Base Flask app factory used by all apps."""
    # Create the Flask application
    app = Flask(__name__, instance_relative_config=False)
    register_extensions(app)
    return app


# def create_webapp() -> Flask:  # pragma: no cover
    """
    Create a version of the app suitable for serving the website locally or in production.
    """


app = Flask(__name__, instance_relative_config=False)
# register_extensions(app)
register_json_routes(app)
register_base_routes(app)
# return app


# app = create_webapp()

if __name__ == "__main__":
    # Start application
    app.run()
