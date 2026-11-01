"""NATS-обработчики сервиса телеметрии."""

import logging

from nats.aio.client import Client as NATS

from common.database import SessionLocal
from common.models import TelemetryReading
from common.nats_client import subscribe_json

log = logging.getLogger(__name__)


async def handle_reading(data: dict):
    """Сохраняет показание из NATS 'telemetry.reading'.

    Формат: {device_id, metric, value, unit}
    """
    async with SessionLocal() as db:
        db.add(
            TelemetryReading(
                device_id=data["device_id"],
                metric=data["metric"],
                value=float(data["value"]),
                unit=data.get("unit"),
            )
        )
        await db.commit()
    log.info("Saved reading: %s", data)


async def register_handlers(nc: NATS) -> None:
    """Регистрирует все NATS-подписки сервиса."""
    await subscribe_json(nc, "telemetry.reading", handle_reading)
