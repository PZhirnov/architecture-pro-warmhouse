from flask import Flask

from app.config import Config, get_config


def create_app(config_name: str | None = None) -> Flask:
    """Фабрика приложения. Позволяет создавать инстансы с разным конфигом."""
    app = Flask(__name__)

    config_class: type[Config] = get_config(config_name)
    app.config.from_object(config_class)

    from app.routes import register_routes
    register_routes(app)

    return app
