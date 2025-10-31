"""Panel composition module.

Single source for laying out all sections (devices, weather, electricity,
dishes, garbage). Both file-output (`to_image.py`) and hardware display
(`to_display.py`) should call `compose_panel()` to avoid drift.

Usage:
    from compose import compose_panel
    img = compose_panel()
    img.save("main.png")            # for image output
    epd.display(epd.getbuffer(img))  # for hardware

Notes:
- Keeps width/height/padding constants here to avoid magic numbers scattered.
- Devices list is passed in so external events (MQTT) can modify state.
- All drawing functions mutate a shared ImageDraw instance.
"""

from PIL import Image, ImageDraw
from devices import draw_device_icons
from weather import draw_weather
from electricity_price import draw_electricity_price
from dishes import draw_weekly_dishes
from garbage import draw_garbage_collection
from last_update import draw_last_update
from typing import Callable

WIDTH, HEIGHT = 800, 480
PADDING = 16

def _safe(func: Callable, label: str, *args, **kwargs):
    """Execute a drawing function safely, logging any exception and continuing.

    Keeps composition resilient so a failing section doesn't break the whole panel.
    """
    try:
        func(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 (broad ok: we want to catch all rendering issues)
        print(f"[COMPOSE][ERROR] Section '{label}' failed: {e}")


def compose_panel():
    """Create and return a fully rendered PIL Image.

    Returns:
        PIL.Image: Rendered grayscale image ready for saving or display.
    """
    image = Image.new("L", (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    # Devices (left column)
    _safe(draw_device_icons, "devices", draw, (PADDING, PADDING))

    # Weather (center-left)
    _safe(draw_weather, "weather", draw, (PADDING + 36 * 2, PADDING))

    # Electricity price + consumption (right top)
    _safe(draw_electricity_price, "electricity", draw, (PADDING + 500, PADDING))

    # Weekly dishes (below weather)
    _safe(draw_weekly_dishes, "dishes", draw, (PADDING + 36 * 2, PADDING + 270))

    # Garbage collection (below electricity charts)
    _safe(draw_garbage_collection, "garbage", draw, (PADDING + 500, PADDING + 280))

    # Last updated timestamp (bottom-right corner, subtle)
    _safe(draw_last_update, "last_update", draw, (WIDTH - PADDING, HEIGHT - PADDING))

    return image

__all__ = ["compose_panel", "WIDTH", "HEIGHT", "PADDING"]
