import os


class Config:
    """Базовая конфигураця"""
    DEBUG = False
    TESTING = False
    # Диапазон генерации температур
    TEMP_MAX = 26.0
    TEMP_MIN = 18.0


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    """Возвращает класс конфигурации по имени (или из переменной окружения)."""
    name = name or os.getenv("FLASK_ENV", "default")
    return CONFIG_MAP.get(name, DevelopmentConfig)
