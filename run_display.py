"""
Display runner: orchestrates MQTT + periodic refresh and delegates all
hardware rendering logic to `DisplayController` (see display_controller.py).

Structure mirrors run_dev.py but uses the hardware pipeline.
Future extension: add physical button listener thread.
"""

import time
import sys
import threading
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw

from config import (
    MQTT_DEVICE_TOPICS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_PREFIX,
)
from devices import update_device_by_topic, get_devices_region
from compose import PADDING, HEIGHT, WIDTH
from display_controller import DisplayController

def button_listener(controller: DisplayController):
    # Placeholder for GPIO integration
    while not controller.stopped:
        time.sleep(2)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected")
        if MQTT_TOPIC_PREFIX:
            wildcard = f"{MQTT_TOPIC_PREFIX}/#"
            client.subscribe(wildcard)
            print(f"[MQTT] Subscribed to {wildcard}")
        for t in MQTT_DEVICE_TOPICS:
            client.subscribe(t)
            print(f"[MQTT] Subscribed to {t}")
    else:
        print(f"[MQTT] Connect failed rc={rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip().lower()
    print(f"[MQTT] {topic} => {payload}")

    if topic in MQTT_DEVICE_TOPICS and payload in {"on", "off"}:
        updated = update_device_by_topic(topic, payload == "on")
        if updated and userdata:
            region_img, bbox = get_devices_region(PADDING, HEIGHT)
            userdata.partial_update(region_img, bbox)

def main():
    print("[INIT] Starting display runner (E-Ink mode)")
    controller = DisplayController()
    controller.render()

    client = mqtt.Client(userdata=controller)
    # Apply credentials if configured
    if MQTT_USERNAME is not None:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or "")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        print(f"[ERROR] MQTT connection failed: {e}")
        sys.exit(1)

    client.loop_start()

    # Periodic full refresh thread (hourly or configured interval)
    stop_event = threading.Event()
    def refresh_loop():
        while not stop_event.is_set():
            time.sleep(3600)  # fixed 1h; can be changed to REFRESH_INTERVAL if desired
            if stop_event.is_set():
                break
            controller.render()
    threading.Thread(target=refresh_loop, daemon=True).start()
    # threading.Thread(target=button_listener, args=(controller,), daemon=True).start()

    print("[RUNNING] Press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping...")
        stop_event.set()
        controller.stop()
        client.loop_stop()
        client.disconnect()
        print("[SHUTDOWN] Done")


if __name__ == "__main__":
    main()
