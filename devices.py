"""Device rendering & state utilities.

Devices are defined centrally in `config.py` (`DEVICES_CONFIG`) with Swedish
labels and MQTT topics. This module maintains an in-memory mutable copy
including current `on` status.

Device dict shape:
{
  "label": "Tvättmaskin",      # Swedish label
  "topic": "statechange/washing_machine",  # MQTT topic string
  "icon": "\ue832",            # Glyph from loaded icon font
  "on": True                     # Boolean status; off => light_gray icon
}
"""

from PIL import Image, ImageDraw, ImageFont
from gui_constant import colors, icon_size, icon_font, text_font
from config import DEVICES_CONFIG

# Global in-memory device list initialized from config
DEVICES = [
    {"label": d["label"], "icon": d["icon"], "on": d["on"], "topic": d["topic"]}
    for d in DEVICES_CONFIG
]

def draw_device_icons(draw, pos):
    """Draw a vertical list of device icons.

    Args:
        draw: PIL ImageDraw instance (shared composition buffer)
        pos: (x, y) top-left anchor for the list
    """
    box_padding = 4
    box_height = icon_size + box_padding * 2

    icon_y_offset = pos[1]
    for device in DEVICES:
        y = icon_y_offset
        icon_color = colors["black"] if device.get("on") else colors["light_gray"]
        draw.text((pos[0], y), device.get("icon", "?"), font=icon_font, fill=icon_color)

        icon_y_offset += box_height

def get_devices_region(padding, full_height):
    """Return a cropped devices column image and its bbox within the full panel.

    Args:
        padding (int): Outer panel padding.
        full_height (int): Total panel height.

    Returns:
        (PIL.Image, tuple): (region_img, bbox)
            bbox format: (x1, y1, x2, y2)
    """
    devices_width = icon_size * 2  # conservative 2-column width
    bbox = (padding, padding, padding + devices_width, full_height - padding)
    region_img_height = full_height - 2 * padding
    region_img = Image.new("L", (devices_width, region_img_height), colors["white"])
    region_draw = ImageDraw.Draw(region_img)
    draw_device_icons(region_draw, (0, 0))
    return region_img, bbox

def update_device_state(label, on):
    """Update a device's on/off status by label. Returns global list."""
    for d in DEVICES:
        if d.get("label") == label:
            d["on"] = bool(on)
            return DEVICES
    # If label not found, append minimal entry (topic unknown)
    DEVICES.append({"label": label, "icon": "\ue832", "on": bool(on), "topic": None})
    return DEVICES

def update_device_by_topic(topic, on):
    """Update device state matching a given MQTT topic. Returns device or None."""
    for d in DEVICES:
        on_bool = bool(on)
        if d.get("topic") == topic and d.get("on") != on_bool:
            print(f"[DEVICE] Updating '{d.get('label')}' ({topic}) to {'ON' if on else 'OFF'}")
            d["on"] = on_bool
            return d
    return None

__all__ = [
    "draw_device_icons",
    "update_device_state",
    "update_device_by_topic",
    "DEVICES",
    "get_devices_region",
]
