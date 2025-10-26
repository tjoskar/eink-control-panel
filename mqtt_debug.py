"""Simple MQTT debugging script.

Connects to the broker defined in config.py (MQTT_HOST, MQTT_PORT), subscribes to all
topics ("#") and prints every received message with timestamp.

If the topic matches one of the device topics in MQTT_DEVICE_TOPICS it prints extra
info including the device label and interpreted on/off state if payload is boolean-like.

Usage:
    python mqtt_debug.py

Optional environment variables for quick override (kept minimal):
    MQTT_HOST, MQTT_PORT

Note: This is a lightweight debug helper; no reconnection backoff sophistication.
"""
from __future__ import annotations
import socket
import os
import sys
import json
import time
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

from config import (
    MQTT_HOST as CFG_HOST,
    MQTT_PORT as CFG_PORT,
    MQTT_USERNAME as CFG_USER,
    MQTT_PASSWORD as CFG_PASS,
    MQTT_TOPIC_PREFIX,
    DEVICES_CONFIG,
    MQTT_DEVICE_TOPICS,
)

# Resolve host/port (allow quick override via env for testing without editing config)
HOST = os.getenv("MQTT_HOST", CFG_HOST)
try:
    PORT = int(os.getenv("MQTT_PORT", str(CFG_PORT)))
except ValueError:
    print("Invalid MQTT_PORT env var; falling back to config value", file=sys.stderr)
    PORT = CFG_PORT

# Optional credentials (env overrides config). Empty strings treated as None.
USER = os.getenv("MQTT_USERNAME", CFG_USER if CFG_USER is not None else "") or None
PASS = os.getenv("MQTT_PASSWORD", CFG_PASS if CFG_PASS is not None else "") or None

# Build map topic -> device config for fast lookup
DEVICE_BY_TOPIC = {d["topic"]: d for d in DEVICES_CONFIG}

# Simple helpers

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _interpret_payload(raw: bytes) -> Any:
    """Try to decode payload into a useful Python object.
    - UTF-8 decode
    - Attempt JSON if starts with '{' or '['
    - Normalize common boolean strings
    """
    try:
        text = raw.decode("utf-8", errors="replace").strip()
    except Exception:
        return raw

    if not text:
        return ""  # empty

    lowered = text.lower()
    if lowered in {"on", "off", "true", "false", "1", "0"}:
        if lowered in {"on", "true", "1"}:
            return True
        return False

    if text[0] in "[{" and text[-1] in "]}":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return text


def on_connect(client: mqtt.Client, userdata, flags, rc):  # type: ignore[override]
    if rc == 0:
        print(f"[{_ts()}] Connected to MQTT {HOST}:{PORT}")
        # Decide subscription pattern based on prefix config (env override allowed)
        env_prefix = os.getenv("MQTT_TOPIC_PREFIX")
        prefix = env_prefix if env_prefix is not None else MQTT_TOPIC_PREFIX
        if prefix:
            sub_pattern = f"{prefix}/#"
        else:
            sub_pattern = "#"
        client.subscribe(sub_pattern)
        print(f"[{_ts()}] Subscribed to '{sub_pattern}'")
    else:
        print(f"[{_ts()}] Connection failed (rc={rc})", file=sys.stderr)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):  # type: ignore[override]
    payload_obj = _interpret_payload(msg.payload)
    base_line = f"[{_ts()}] TOPIC={msg.topic} QOS={msg.qos} RETAIN={int(msg.retain)} PAYLOAD={payload_obj!r}"

    if msg.topic in DEVICE_BY_TOPIC:
        device = DEVICE_BY_TOPIC[msg.topic]
        # Derive potential on/off state from payload if boolean-like
        state_str = "unknown"
        if isinstance(payload_obj, bool):
            state_str = "ON" if payload_obj else "OFF"
        elif isinstance(payload_obj, (int, str)):
            lowered = str(payload_obj).lower()
            if lowered in {"on", "true", "1"}:
                state_str = "ON"
            elif lowered in {"off", "false", "0"}:
                state_str = "OFF"
        extra = f" <DEVICE label='{device['label']}' state={state_str}>"
        print(base_line + extra)
    else:
        print(base_line)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Apply credentials if provided
    if USER is not None:
        client.username_pw_set(USER, PASS or "")

    try:
        client.connect(HOST, PORT, keepalive=60)
    except Exception as e:
        print(f"[{_ts()}] Could not connect to MQTT broker {HOST}:{PORT} -> {e}", file=sys.stderr)
        sys.exit(1)

    # Blocking loop; Ctrl+C to exit
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"[{_ts()}] Interrupted; disconnecting...")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()
