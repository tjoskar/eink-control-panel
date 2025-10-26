"""Panel composition module.

Single source for laying out all sections (devices, weather, electricity,
dishes, garbage). Both file-output (`to-image.py`) and hardware display
(`to-disply.py`) should call `compose_panel(devices)` to avoid drift.

Usage:
    from compose import compose_panel
    img = compose_panel(devices)
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

WIDTH, HEIGHT = 800, 480
PADDING = 16

def compose_panel():
    """Create and return a fully rendered PIL Image.
    Returns:
        PIL.Image: Rendered grayscale image ready for saving or display.
    """
    image = Image.new("L", (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    # Devices (left column)
    draw_device_icons(draw, (PADDING, PADDING))

    # Weather (center-left)
    draw_weather(draw, (PADDING + 36 * 2, PADDING))

    # Electricity price + consumption (right top)
    draw_electricity_price(draw, (PADDING + 500, PADDING))

    # Weekly dishes (below weather)
    draw_weekly_dishes(draw, (PADDING + 36 * 2, PADDING + 270))

    # Garbage collection (below electricity charts)
    draw_garbage_collection(draw, (PADDING + 500, PADDING + 280))

    return image

__all__ = ["compose_panel", "WIDTH", "HEIGHT", "PADDING"]
