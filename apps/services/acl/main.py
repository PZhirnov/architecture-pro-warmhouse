import asyncio
import json
import logging
from contextlib import asynccontextmanager

import paho.mqtt.client as mqtt
from fastapi import FastAPI

from common.config import settings
from common.nats_client import connect, publish_json

log = logging.getLogger(__name__)

MQTT_TOPIC = "smarthome/telemetry"
NATS_SUBJECT = "telemetry.reading"

_nc = None
_mqtt = None
_loop: asyncio.AbstractEventLoop | None = None


def _on_connect(client, userdata, flags, rc, props=None):
    log.info("MQTT connected rc=%s", rc)
    client.subscribe(MQTT_TOPIC, qos=1)
    log.info("Subscribed to %s", MQTT_TOPIC)


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        log.exception("Bad JSON from MQTT: %r", msg.payload)
        return

    if _loop is None or _nc is None:
        log.warning("NATS not ready, drop message")
        return

    asyncio.run_coroutine_threadsafe(
        publish_json(_nc, NATS_SUBJECT, payload), _loop
    )
    log.info("Bridged → %s", payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nc, _mqtt, _loop
    _loop = asyncio.get_running_loop()

    _nc = await connect()

    _mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="acl")
    _mqtt.on_connect = _on_connect
    _mqtt.on_message = _on_message
    _mqtt.reconnect_delay_set(min_delay=1, max_delay=10)

    async def _connect_mqtt():
        while True:
            try:
                _mqtt.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
                _mqtt.loop_start()
                log.info("MQTT bridge started")
                return
            except Exception as e:
                log.warning("MQTT connect failed (%s), retry in 3s", e)
                await asyncio.sleep(3)

    mqtt_task = asyncio.create_task(_connect_mqtt())

    yield

    mqtt_task.cancel()
    if _mqtt:
        _mqtt.loop_stop()
        _mqtt.disconnect()
    if _nc:
        await _nc.drain()


app = FastAPI(title="ACL Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "service": "acl",
        "status": "ok",
        "mqtt_connected": bool(_mqtt and _mqtt.is_connected()),
        "nats_connected": bool(_nc and _nc.is_connected),
    }
