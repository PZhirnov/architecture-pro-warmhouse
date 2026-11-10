# services/automation/handlers.py
import logging
from typing import Any

from nats.aio.client import Client as NATS

from common.config import settings
from common.nats_client import publish_json

log = logging.getLogger(__name__)


def _as_bool(value: Any) -> bool:
    """true/1/'on'/'open'/'yes' → True."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on", "open")
    return bool(value)


async def handle_reading(nc: NATS, data: dict) -> None:
    """Правила автоматизации. Каждое — независимый elif по metric."""
    metric = data.get("metric")
    value = data.get("value")
    device_id = data.get("device_id")
    room = data.get("room", "unknown")

    # --- 1. Температура: слишком жарко → выключить обогрев этого устройства
    if metric == "temperature" and float(value) > settings.temperature_threshold:
        log.info("Rule: temp %.1f > %.1f on device %s",
                 float(value), settings.temperature_threshold, device_id)
        await publish_json(
            nc, "device.command",
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
            nc, "device.command",
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
            nc, "device.command",
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
            nc, "device.command",
            {
                "device_id": target,
                "command": "light_on",
                "reason": f"illuminance {value} < {settings.illuminance_threshold} in {room}",
            },
        )

    # --- 5. Утечка воды: авария → закрыть клапан
    elif metric == "water_leak" and _as_bool(value):
        target = f"valve-{room}"
        log.warning("Rule: WATER LEAK in %s → %s", room, target)
        await publish_json(
            nc, "device.command",
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
            nc, "device.command",
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
            nc, "device.command",
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
            nc, "notification.command",
            {
                "device_id": device_id,
                "command": "notify",
                "reason": f"battery {value} < {settings.battery_threshold}",
            },
        )
