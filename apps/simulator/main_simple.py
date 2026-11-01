import json
import logging
import os
import random
import time

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sim")

HOST = os.getenv("MQTT_URL", "mqtt")
PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL = int(os.getenv("INTERVAL_SEC", "1"))

DEVICES = [
    {"device_id": 1, "metric": "temperature", "unit": "°C", "base": 22, "jitter": 6},
    {"device_id": 1, "metric": "humidity",    "unit": "%",  "base": 45, "jitter": 10},
    {"device_id": 2, "metric": "temperature", "unit": "°C", "base": 20, "jitter": 8},
]


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulator")
    while True:
        try:
            client.connect(HOST, PORT, 60)
            break
        except Exception as e:
            log.warning("MQTT not ready (%s), retry in 3s", e)
            time.sleep(3)

    client.loop_start()
    log.info("Simulator connected to %s:%s, interval=%ss", HOST, PORT, INTERVAL)

    while True:
        for d in DEVICES:
            value = round(d["base"] + random.uniform(-d["jitter"], d["jitter"]), 1)
            msg = {
                "device_id": d["device_id"],
                "metric": d["metric"],
                "value": value,
                "unit": d["unit"],
            }
            client.publish("smarthome/telemetry", json.dumps(msg))
            log.info("Publish %s", msg)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
