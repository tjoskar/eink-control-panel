"""Simple MQTT listener that updates device states and regenerates the image.

Lyssnar på ämnet (topic):
  statechange/washing_machine
Payload förväntas vara "on" eller "off".
När status ändras kör vi `generate_image(devices)` igen.

Keep it minimal: no persistence, no reconnect strategy beyond paho defaults.
"""

import json
import sys
from typing import List, Dict

import paho.mqtt.client as mqtt

from devices import update_device_state, get_devices
from compose import compose_panel

MQTT_HOST = "localhost"  # Dummy value; replace with actual broker host
MQTT_PORT = 1883          # Standard MQTT port
TOPIC_WASHING_MACHINE = "statechange/washing_machine"


def regenerate():
    """Regenerate PNG image using current global device states."""
    devices = get_devices()
    image = compose_panel(devices)
    image.save("main.png")
    print("[INFO] Image regenerated with updated device states.")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Connected to MQTT broker.")
        client.subscribe(TOPIC_WASHING_MACHINE)
        print(f"[INFO] Subscribed to {TOPIC_WASHING_MACHINE}")
    else:
        print(f"[ERROR] Connection failed (rc={rc})")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip().lower()
    print(f"[DEBUG] Message received: {topic} => {payload}")

    if topic == TOPIC_WASHING_MACHINE:
        if payload in {"on", "off"}:
            update_device_state(get_devices(), "Washing Machine", payload == "on")
            regenerate()
        else:
            print(f"[WARN] Unexpected payload: {payload}")


def main():
    regenerate()  # Generate initial image

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        print(f"[ERROR] Could not connect to MQTT broker: {e}")
        sys.exit(1)

    # Blocking loop
    client.loop_forever()


if __name__ == "__main__":
    main()
