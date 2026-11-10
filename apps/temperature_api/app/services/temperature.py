"""Бизнес-логика: разрешение location/sensorId и генерация температуры."""

import random
from datetime import datetime, timezone

from flask import current_app

from app.data.sensors import (
    DEFAULT_LOCATION,
    DEFAULT_SENSOR_ID,
    LOCATION_TO_SENSOR,
    SENSOR_TO_LOCATION,
)

# Если в запросе передаетсся только id датчика
def resolve_location(location: str, sensor_id: str) -> str:
    """Если location пуст — определяем по sensorId."""
    if not location:
        return SENSOR_TO_LOCATION.get(sensor_id, DEFAULT_LOCATION)
    return location


def resolve_sensor_id(location: str, sensor_id: str) -> str:
    """Если sensorId пуст — определяем по location."""
    if not sensor_id:
        return LOCATION_TO_SENSOR.get(location, DEFAULT_SENSOR_ID)
    return sensor_id


def generate_temperature() -> float:
    """Случайная температура в диапазоне из конфига, с одним знаком после запятой."""
    temp_min = current_app.config["TEMP_MIN"]
    temp_max = current_app.config["TEMP_MAX"]
    return round(random.uniform(temp_min, temp_max), 1)


def get_temperature(location: str, sensor_id: str) -> dict:
    """Полный сценарий: разрешаем параметры и генерируем температуру."""
    location = resolve_location(location, sensor_id)
    sensor_id = resolve_sensor_id(location, sensor_id)
    value = generate_temperature()

    return {
        "location": location,
        "sensor_id": sensor_id, # оставляем — Go его игнорирует
        "value": value,
        "unit": "°C",
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "description": f"Температура для сенсора {sensor_id}",
    }
