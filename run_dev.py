"""Development runner: generates PNG image, listens for MQTT events, and
periodically refreshes the dashboard.

Future extension: add physical button event handling (thread placeholder).

Responsibilities:
- Initial render to main.png
- Subscribe to topics (statechange/washing_machine)
- On message: update device state + re-render
- Periodic full refresh every REFRESH_INTERVAL seconds

Keeps threading simple: one MQTT network loop (loop_start) + one refresh
thread + optional future button thread.
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

_render_lock = threading.Lock()
_stop_event = threading.Event()
_render_timer = None


def render_png():
    """Render current state to main.png (thread-safe)."""
    with _render_lock:
        img = compose_panel()
        img.save("main.png")
        print("[RENDER] main.png updated")


def schedule_render():
    """Debounce rendering by scheduling a timer. Rapid successive updates reset the timer."""
    global _render_timer
    # Cancel previous timer if exists
    if _render_timer is not None:
        _render_timer.cancel()
    def _do():
        render_png()
    _render_timer = threading.Timer(MQTT_RENDER_DEBOUNCE_SECONDS, _do)
    _render_timer.daemon = True
    _render_timer.start()
    print(f"[DEBOUNCE] Render scheduled in {MQTT_RENDER_DEBOUNCE_SECONDS}s")


def refresh_loop():
    """Periodic refresh loop; exits when _stop_event is set."""
    while not _stop_event.is_set():
        time.sleep(REFRESH_INTERVAL)
        if _stop_event.is_set():
            break
        print(f"[TIMER] Refresh interval reached ({REFRESH_INTERVAL}s)")
        render_png()


def button_listener():
    """Placeholder for future physical button events.

    Design idea: poll GPIO or use interrupts; when event triggers, call
    render_png() or toggle a device state.
    Currently sleeps to avoid busy loop.
    """
    while not _stop_event.is_set():
        time.sleep(2)
        # Future: integrate actual GPIO logic here.


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected")
        # If prefix configured, subscribe wildcard to catch new devices quickly; still subscribe explicit list for clarity.
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
        else:
            print(f"[WARN] Topic {topic} not mapped to device list")


def main():
    print("[INIT] Starting development runner (PNG mode)")
    render_png()

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

    # Start MQTT network loop thread
    client.loop_start()

    # Start periodic refresh thread
    threading.Thread(target=refresh_loop, daemon=True).start()

    # Start placeholder button listener (future extension)
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
        try:
            if _render_timer is not None:
                _render_timer.cancel()
        except Exception:
            pass
        print("[SHUTDOWN] Done")


if __name__ == "__main__":
    main()
