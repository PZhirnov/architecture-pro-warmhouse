from flask import Flask

from . import temperature


def register_routes(app: Flask) -> None:
    app.register_blueprint(temperature.bp)
