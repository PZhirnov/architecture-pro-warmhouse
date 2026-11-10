import asyncio
import json
import logging
import os
import random
import time

import paho.mqtt.client as mqtt
from sqlalchemy import select

from common.database import SessionLocal
from common.models import Device

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sim")

MQTT_HOST = os.getenv("MQTT_URL", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SEC = int(os.getenv("INTERVAL_SEC", "5"))
RELOAD_SEC = int(os.getenv("RELOAD_SEC", "60"))
MQTT_TOPIC = "smarthome/telemetry"


# ============================================================
# Профили метрик по типу/модели устройства
# ============================================================
def metrics_for_device(d: dict) -> list[dict]:
    """
    Возвращает список профилей метрик, которые генерирует это устройство.
    Пустой список — устройство не эмитит телеметрию (например, gateway).
    """
    model = (d.get("model") or "").lower()
    typ = d["type"]

    if typ == "sensor":
        if "motion" in model:
            return [{"metric": "motion", "unit": None,
                     "gen": "binary", "p_true": 0.15}]
        if "temperature" in model or "monitor" in model or "temp" in model:
            return [
                {"metric": "temperature", "unit": "°C",
                 "gen": "gauss", "base": 22.0, "std": 2.0},
                {"metric": "humidity", "unit": "%",
                 "gen": "gauss", "base": 45.0, "std": 5.0},
            ]
        return [{"metric": "temperature", "unit": "°C",
                 "gen": "gauss", "base": 22.0, "std": 2.0}]

    if typ == "actuator":
        if "plug" in model or "relay" in model:
            return [
                {"metric": "power", "unit": "W",
                 "gen": "gauss", "base": 120.0, "std": 20.0},
                {"metric": "switch", "unit": None,
                 "gen": "binary", "p_true": 0.7},
            ]
        return [{"metric": "power", "unit": "W",
                 "gen": "gauss", "base": 100.0, "std": 15.0}]

    if typ == "camera":
        return [{"metric": "recording", "unit": None,
                 "gen": "binary", "p_true": 0.9}]

    # gateway — не генерирует телеметрию
    return []


def gen_value(profile: dict) -> float | int:
    gen = profile["gen"]
    if gen == "gauss":
        return round(random.gauss(profile["base"], profile["std"]), 1)
    if gen == "binary":
        return 1 if random.random() < profile["p_true"] else 0
    return 0


# ============================================================
# MQTT — подключение с ретраями
# ============================================================
async def _mqtt_connect(client: mqtt.Client) -> None:
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            log.info("MQTT connected to %s:%s", MQTT_HOST, MQTT_PORT)
            return
        except Exception as e:
            log.warning("MQTT not ready (%s), retry in 3s", e)
            await asyncio.sleep(3)


# ============================================================
# Загрузка «рабочего набора» из БД
# ============================================================
async def _load_workload() -> list[dict]:
    """
    Читает все устройства из БД, разворачивает в плоский список
    (device_id, profile) — одна запись на каждую метрику устройства.
    """
    while True:
        try:
            async with SessionLocal() as db:
                rows = (await db.execute(select(Device))).scalars().all()
            break
        except Exception as e:
            log.warning("DB not ready (%s), retry in 3s", e)
            await asyncio.sleep(3)

    workload: list[dict] = []
    for d in rows:
        dev = {"type": d.type, "vendor": d.vendor, "model": d.model}
        for p in metrics_for_device(dev):
            workload.append({"device_id": d.id, **p})

    log.info(
        "Loaded %d devices → %d metric profiles (skipped: %d)",
        len(rows),
        len(workload),
        len(rows) - sum(1 for d in rows if metrics_for_device(d.__dict__)),
    )
    return workload


# ============================================================
# Основной цикл
# ============================================================
async def run() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulator")
    await _mqtt_connect(client)

    workload = await _load_workload()
    if not workload:
        log.warning("Workload is empty — nothing to publish. "
                    "Add devices to DB or change metrics_for_device()")

    log.info("Simulator running: interval=%ss, reload=%ss", INTERVAL_SEC, RELOAD_SEC)

    last_reload = time.monotonic()
    published = 0

    while True:
        for w in workload:
            value = gen_value(w)
            msg = {
                "device_id": w["device_id"],
                "metric": w["metric"],
                "value": value,
                "unit": w.get("unit"),
            }
            client.publish(MQTT_TOPIC, json.dumps(msg))
            published += 1

        log.info("Published %d messages (total: %d)", len(workload), published)

        # Периодическая перезагрузка списка устройств
        if time.monotonic() - last_reload >= RELOAD_SEC:
            try:
                workload = await _load_workload()
                last_reload = time.monotonic()
            except Exception:
                log.exception("Reload failed, keep previous workload")

        await asyncio.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("Stopped")
