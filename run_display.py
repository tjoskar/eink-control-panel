"""
Display runner: renders directly to E-Ink hardware, listens for MQTT,
and performs periodic refreshes.

Structure mirrors run_dev.py but uses the hardware pipeline.
Future extension: add physical button listener thread.
"""

import time
import threading
import sys
import paho.mqtt.client as mqtt

from config import (
    REFRESH_INTERVAL,
    MQTT_DEVICE_TOPICS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_PREFIX,
    MQTT_RENDER_DEBOUNCE_SECONDS,
)
from devices import update_device_by_topic
from compose import compose_panel

# Waveshare driver import only when actually used (avoid cost if imported elsewhere)
from lib.waveshare_epd.epd7in5_V2 import EPD


_render_lock = threading.Lock()
_stop_event = threading.Event()
_render_timer = None  # type: ignore
_epd = None


def init_display():
    global _epd
    _epd = EPD()
    _epd.init()
    _epd.Clear()
    print("[DISPLAY] Initialized and cleared")


def render_display():
    with _render_lock:
        img = compose_panel()
        _epd.display(_epd.getbuffer(img))
        print("[RENDER] Display updated")


def schedule_render():
    """Debounce display rendering to batch rapid retained messages."""
    global _render_timer
    if _render_timer is not None:
        _render_timer.cancel()
    def _do():
        render_display()
    _render_timer = threading.Timer(MQTT_RENDER_DEBOUNCE_SECONDS, _do)
    _render_timer.daemon = True
    _render_timer.start()
    print(f"[DEBOUNCE] Display render scheduled in {MQTT_RENDER_DEBOUNCE_SECONDS}s")


def refresh_loop():
    while not _stop_event.is_set():
        time.sleep(REFRESH_INTERVAL)
        if _stop_event.is_set():
            break
        print(f"[TIMER] Refresh interval reached ({REFRESH_INTERVAL}s)")
        render_display()


def button_listener():
    # Placeholder for GPIO integration
    while not _stop_event.is_set():
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
        if updated:
            schedule_render()

def main():
    print("[INIT] Starting display runner (E-Ink mode)")
    init_display()
    render_display()

    client = mqtt.Client()
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

    threading.Thread(target=refresh_loop, daemon=True).start()
    threading.Thread(target=button_listener, daemon=True).start()

    print("[RUNNING] Press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping...")
        _stop_event.set()
        client.loop_stop()
        client.disconnect()
        if _epd:
            _epd.sleep()
        try:
            if _render_timer is not None:
                _render_timer.cancel()
        except Exception:
            pass
        print("[SHUTDOWN] Done")


if __name__ == "__main__":
    main()
