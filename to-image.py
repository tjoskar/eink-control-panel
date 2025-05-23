from PIL import Image, ImageDraw, ImageFont
from constant import colors
from devices import draw_device_icons
from weather import draw_weather
from electricity_price import draw_electricity_price
from dishes import draw_weekly_dishes
from garbage import draw_garbage_collection

# Image
width, height = 800, 480
image = Image.new("L", (width, height), 255)
draw = ImageDraw.Draw(image)
padding = 16

draw_device_icons(draw, (padding, padding))
draw_weather(draw, (padding + 36*3, padding))
draw_electricity_price(draw, (padding + 500, padding))
# Draw weekly dishes below the weather section
draw_weekly_dishes(draw, (padding + 36*3, padding + 270))
# Draw garbage collection reminders below the electricity charts
draw_garbage_collection(draw, (padding + 500, padding + 280))

# Save PNG (for testing on Mac)
image.save("main.png")
