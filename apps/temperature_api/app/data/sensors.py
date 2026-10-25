"""Справочники датчиков. В будущем можно заменить на обращение к БД."""

SENSOR_TO_LOCATION: dict[str, str] = {
    "1": "Living Room",
    "2": "Bedroom",
    "3": "Kitchen",
}

LOCATION_TO_SENSOR: dict[str, str] = {
    location: sensor_id for sensor_id, location in SENSOR_TO_LOCATION.items()
}

DEFAULT_LOCATION = "Unknown"
DEFAULT_SENSOR_ID = "0"
