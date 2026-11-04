import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.config import settings
from common.nats_client import connect, publish_json, subscribe_json

log = logging.getLogger(__name__)
_nc = None


async def handle_reading(data: dict):
    """Правила автоматизации. Каждое — независимый if по metric."""
    metric = data.get("metric")
    value = data.get("value")
    device_id = data.get("device_id")
    room = data.get("room", "unknown")

    # --- 1. Температура: слишком жарко → выключить обогрев этого устройства
    if metric == "temperature" and float(value) > settings.temperature_threshold:
        log.info("Rule: temp %.1f > %.1f on device %s",
                 float(value), settings.temperature_threshold, device_id)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": device_id,
                "command": "switch_off",
                "reason": f"temperature {value} > {settings.temperature_threshold}",
            },
        )

    # --- 2. Влажность: высокая → включить осушитель в комнате
    elif metric == "humidity" and float(value) > settings.humidity_threshold:
        target = f"climate-{room}"
        log.info("Rule: humidity %.1f > %.1f in %s → %s",
                 float(value), settings.humidity_threshold, room, target)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": target,
                "command": "dehumidifier_on",
                "reason": f"humidity {value} > {settings.humidity_threshold} in {room}",
            },
        )

    # --- 3. CO2: высокий → включить вентиляцию
    elif metric == "co2" and float(value) > settings.co2_threshold:
        target = f"vent-{room}"
        log.info("Rule: co2 %.0f > %.0f in %s → %s",
                 float(value), settings.co2_threshold, room, target)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": target,
                "command": "ventilation_on",
                "reason": f"co2 {value} > {settings.co2_threshold} in {room}",
            },
        )

    # --- 4. Освещённость: темно → включить свет
    elif metric == "illuminance" and float(value) < settings.illuminance_threshold:
        target = f"light-{room}"
        log.info("Rule: illuminance %.0f < %.0f in %s → %s",
                 float(value), settings.illuminance_threshold, room, target)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": target,
                "command": "light_on",
                "reason": f"illuminance {value} < {settings.illuminance_threshold} in {room}",
            },
        )

    # --- 5. Утечка воды: авария → закрыть клапан, без кулдауна
    elif metric == "water_leak" and _as_bool(value):
        target = f"valve-{room}"
        log.warning("Rule: WATER LEAK in %s → %s", room, target)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": target,
                "command": "valve_close",
                "reason": f"water leak detected in {room}",
            },
        )

    # --- 6. Дым: авария → выключить всё в комнате через сцену
    elif metric == "smoke" and _as_bool(value):
        log.warning("Rule: SMOKE in %s → emergency_off", room)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": f"scene-{room}",
                "command": "emergency_off",
                "reason": f"smoke detected in {room}",
            },
        )

    # --- 7. Движение: есть движение → включить свет
    elif metric == "motion" and _as_bool(value):
        target = f"light-{room}"
        log.info("Rule: motion in %s → %s", room, target)
        await publish_json(
            _nc, "device.command",
            {
                "device_id": target,
                "command": "light_on",
                "reason": f"motion detected in {room}",
            },
        )

    # --- 8. Батарея: разряжена → уведомление (не команда устройству)
    elif metric == "battery" and float(value) < settings.battery_threshold:
        log.info("Rule: battery %.0f%% < %.0f%% on %s",
                 float(value), settings.battery_threshold, device_id)
        await publish_json(
            _nc, "notification.command",
            {
                "device_id": device_id,
                "command": "notify",
                "reason": f"battery {value} < {settings.battery_threshold}",
            },
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc
    _nc = await connect()
    await subscribe_json(_nc, "telemetry.reading", handle_reading)
    yield
    if _nc:
        await _nc.drain()


app = FastAPI(title="Automation Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "service": "automation",
        "status": "ok",
        "temperature_threshold": settings.temperature_threshold,
    }


@app.get("/rules", summary="Список правил автоматизации")
async def list_rules():
    """Полное описание всех активных правил с порогами из конфига."""
    return {
        "service": "automation",
        "subscribed_to": "telemetry.reading",
        "publishes_to": ["device.command", "notification.command"],
        "thresholds": {
            "temperature": settings.temperature_threshold,
            "humidity":    settings.humidity_threshold,
            "co2":         settings.co2_threshold,
            "illuminance": settings.illuminance_threshold,
            "battery":     settings.battery_threshold,
        },
        "rules": [
            {
                "id": 1,
                "name": "auto_switch_off_on_hot",
                "enabled": True,
                "metric": "temperature",
                "condition": f"value > {settings.temperature_threshold}",
                "severity": "info",
                "action": {
                    "type": "device_command",
                    "command": "switch_off",
                    "target": "same device_id",
                    "subject": "device.command",
                },
                "description": "Если температура выше порога — выключить обогрев "
                               "на этом же устройстве.",
                "reason_template": f"temperature {{value}} > {settings.temperature_threshold}",
            },
            {
                "id": 2,
                "name": "auto_dehumidifier_on_high_humidity",
                "enabled": True,
                "metric": "humidity",
                "condition": f"value > {settings.humidity_threshold}",
                "severity": "info",
                "action": {
                    "type": "device_command",
                    "command": "dehumidifier_on",
                    "target": "climate-{room}",
                    "subject": "device.command",
                },
                "description": "Высокая влажность в комнате — включить осушитель "
                               "в этой комнате.",
                "reason_template": f"humidity {{value}} > {settings.humidity_threshold} in {{room}}",
            },
            {
                "id": 3,
                "name": "auto_ventilation_on_high_co2",
                "enabled": True,
                "metric": "co2",
                "condition": f"value > {settings.co2_threshold}",
                "severity": "info",
                "action": {
                    "type": "device_command",
                    "command": "ventilation_on",
                    "target": "vent-{room}",
                    "subject": "device.command",
                },
                "description": "Высокий уровень CO₂ — включить вентиляцию в комнате.",
                "reason_template": f"co2 {{value}} > {settings.co2_threshold} in {{room}}",
            },
            {
                "id": 4,
                "name": "auto_light_on_low_illuminance",
                "enabled": True,
                "metric": "illuminance",
                "condition": f"value < {settings.illuminance_threshold}",
                "severity": "info",
                "action": {
                    "type": "device_command",
                    "command": "light_on",
                    "target": "light-{room}",
                    "subject": "device.command",
                },
                "description": "Темно в комнате — включить свет.",
                "reason_template": f"illuminance {{value}} < {settings.illuminance_threshold} in {{room}}",
            },
            {
                "id": 5,
                "name": "auto_valve_close_on_water_leak",
                "enabled": True,
                "metric": "water_leak",
                "condition": "value == true",
                "severity": "critical",
                "action": {
                    "type": "device_command",
                    "command": "valve_close",
                    "target": "valve-{room}",
                    "subject": "device.command",
                },
                "description": "Обнаружена утечка воды — аварийно закрыть клапан "
                               "в комнате. Срабатывает без задержки.",
                "reason_template": "water leak detected in {room}",
            },
            {
                "id": 6,
                "name": "auto_emergency_off_on_smoke",
                "enabled": True,
                "metric": "smoke",
                "condition": "value == true",
                "severity": "critical",
                "action": {
                    "type": "device_command",
                    "command": "emergency_off",
                    "target": "scene-{room}",
                    "subject": "device.command",
                },
                "description": "Обнаружен дым — выключить всё в комнате через "
                               "сцену. Критическое правило.",
                "reason_template": "smoke detected in {room}",
            },
            {
                "id": 7,
                "name": "auto_light_on_motion",
                "enabled": True,
                "metric": "motion",
                "condition": "value == true",
                "severity": "info",
                "action": {
                    "type": "device_command",
                    "command": "light_on",
                    "target": "light-{room}",
                    "subject": "device.command",
                },
                "description": "Зафиксировано движение — включить свет в комнате.",
                "reason_template": "motion detected in {room}",
            },
            {
                "id": 8,
                "name": "auto_notify_low_battery",
                "enabled": True,
                "metric": "battery",
                "condition": f"value < {settings.battery_threshold}",
                "severity": "warning",
                "action": {
                    "type": "notification",
                    "command": "notify",
                    "target": "same device_id",
                    "subject": "notification.command",
                },
                "description": "Низкий заряд батареи — отправить уведомление "
                               "(не команду устройству).",
                "reason_template": f"battery {{value}} < {settings.battery_threshold}",
            },
        ],
    }
