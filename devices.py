"""Device rendering utilities.

The previous implementation kept a module-level hardcoded list named `devices`.
To support dynamic updates (e.g. via MQTT), callers must now provide a list
of device dictionaries.

Expected device item shape:
{
  "label": "Washing Machine",  # Display label (currently unused in rendering)
  "icon": "\ue832",            # Glyph from loaded icon font
  "on": True                    # Boolean status; off => light_gray icon
}

Rendering only uses icon + on flag. We keep label for potential future
enhancements (like remaining time). Keeping function side-effect free.
"""

from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font

# Global in-memory device list (shared state). Scripts can import DEVICES
# or use get_devices()/update_device to read/modify.
DEVICES = [
    {"label": "Washing Machine", "icon": "\ue832", "on": True},
    {"label": "Tumble Dryer", "icon": "\ue54a", "on": False},
    {"label": "Motorvärmare", "icon": "\ue531", "on": True},
    {"label": "Bike Charger", "icon": "\ueb1b", "on": True},
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

        # Future (example): draw label or remaining time next to icon
        # label = device.get("label")
        # if label:
        #     draw.text((pos[0] + icon_size + 4, y + (icon_size - 16)/2), label, font=text_font, fill=colors["black"])

        icon_y_offset += box_height

def update_device_state(devices, label, on):
    """Update a device's on/off status in-place. If not found, optionally add it.

    Args:
        devices: list of device dicts (mutated if label exists)
        label: device label to match
        on: bool new status
    Returns: devices list (same object for chaining)
    """
    for d in devices:
        if d.get("label") == label:
            d["on"] = bool(on)
            return devices
    # Not found: add minimal entry (could be extended later)
    devices.append({"label": label, "icon": "\ue832", "on": bool(on)})
    return devices

def update_device(label, on):
    """Convenience wrapper to update global DEVICES list."""
    update_device_state(DEVICES, label, on)
    return DEVICES

def get_devices():
    """Return current global device list (reference, not a copy)."""
    return DEVICES

__all__ = ["draw_device_icons", "update_device_state", "update_device", "get_devices", "DEVICES"]
