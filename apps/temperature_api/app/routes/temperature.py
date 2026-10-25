# blueprint с эндпоинтом /temperature

from flask import Blueprint, jsonify, request

from app.services.temperature import get_temperature

bp = Blueprint("temperature", __name__)


@bp.get("/temperature")
def temperature():
    location = request.args.get("location", "").strip()
    sensor_id = request.args.get("sensorId", "").strip()

    result = get_temperature(location=location, sensor_id=sensor_id)
    return jsonify(result)


@bp.get("/temperature/<sensor_id>")
def temperature_by_sensor(sensor_id: str):
    # location из query-строки (если передан), sensorId — из URL
    location = request.args.get("location", "").strip()

    result = get_temperature(location=location, sensor_id=sensor_id)
    return jsonify(result)