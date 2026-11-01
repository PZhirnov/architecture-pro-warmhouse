import json
import logging

import nats
from nats.aio.client import Client as NATS

from common.config import settings

log = logging.getLogger(__name__)


async def connect() -> NATS:
    nc = await nats.connect(settings.nats_url, max_reconnect_attempts=-1)
    log.info("Connected to NATS at %s", settings.nats_url)
    return nc


async def publish_json(nc: NATS, subject: str, data: dict) -> None:
    await nc.publish(subject, json.dumps(data, default=str).encode())


async def subscribe_json(nc: NATS, subject: str, handler) -> None:
    """handler(data: dict) — обычная async-функция."""

    async def _cb(msg):
        try:
            data = json.loads(msg.data.decode())
        except Exception:
            log.exception("Bad message on %s", msg.subject)
            return
        try:
            await handler(data)
        except Exception:
            log.exception("Handler error on %s", msg.subject)

    await nc.subscribe(subject, cb=_cb)
    log.info("Subscribed: %s", subject)
