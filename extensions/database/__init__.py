import os

import extensions


def register_db(app):
    with app.app_context():
        # Initialize SQLAlchemy
        # app.config[
        #     "SQLALCHEMY_DATABASE_URI"
        # ] = "postgres+psycopg2://postgres:password@localhost:54322/paper_trading"
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://vumydpetmqpztk:bfa00ab1b7144321090e28438f3711cea7c574d86606d492b8f75024c75a3573@ec2-52-5-1-20.compute-1.amazonaws.com:5432/da1fdsuokqrg9c"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 1800}
        extensions.db.init_app(app)
        extensions.db.create_all()
