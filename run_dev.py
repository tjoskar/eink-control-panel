"""Development runner: PNG mode + MQTT updates + periodic refresh.

Simplified threading: MQTT loop + hourly refresh thread (placeholder for future buttons).
"""

import time
import sys
import threading
import signal
import paho.mqtt.client as mqtt

class EPD:  # minimal mock matching methods used by DisplayController
    width = 800
    height = 480
    def init(self): pass
    def init_fast(self): pass
    def Clear(self): pass
    def display(self, buf): buf.save("main.png")
    def sleep(self): pass
    def getbuffer(self, image): return image

from config import (
    MQTT_DEVICE_TOPICS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_PREFIX,
)
from devices import update_device_by_topic
from display_controller import DisplayController


def button_listener(controller: DisplayController):
    # Placeholder (no GPIO in dev mode)
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
            userdata.fast_render()

def main():
    print("[INIT] Starting display runner (E-Ink mode)")
    epd = EPD()
    controller = DisplayController(epd)
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

    # Periodic full refresh (fixed 1h; could use REFRESH_INTERVAL)
    stop_event = threading.Event()
    def refresh_loop():
        while not stop_event.is_set():
            time.sleep(3600)  # fixed 1h; can be changed to REFRESH_INTERVAL if desired
            if stop_event.is_set():
                break
            controller.render()
    threading.Thread(target=refresh_loop, daemon=True).start()
    # threading.Thread(target=button_listener, args=(controller,), daemon=True).start()

    # Unified shutdown routine
    def shutdown(reason: str):
        print(f"\n[SHUTDOWN] {reason}...")
        stop_event.set()
        controller.stop()
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass
        print("[SHUTDOWN] Done")

    # Signal handlers (SIGINT, SIGTERM)
    def handle_signal(signum, frame):
        name = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}.get(signum, str(signum))
        shutdown(f"Received {name}")
        # Exit immediately after cleanup
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print("[RUNNING] Press Ctrl+C or send SIGTERM to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown("KeyboardInterrupt")
    except Exception as e:
        shutdown(f"Unhandled exception: {e}")


if __name__ == "__main__":
    main()
