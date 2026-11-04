import logging

from nats.aio.client import Client as NATS

from common.database import SessionLocal
from common.nats_client import subscribe_json
from services.device.services.command_service import record_command

log = logging.getLogger(__name__)


async def handle_command(data: dict):
    """NATS 'device.command': {device_id, command, reason}."""
    device_id = data["device_id"]
    command = data["command"]
    reason = data.get("reason")

    async with SessionLocal() as db:
        await record_command(db, device_id, command, reason)

    # Передачу команды в очередь для устройства добавить можно тут или разнести на слои

    log.info("Executed %s on device %s (reason: %s)", command, device_id, reason)


async def register_handlers(nc: NATS) -> None:
    await subscribe_json(nc, "device.command", handle_command)
    