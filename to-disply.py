from lib.waveshare_epd.epd7in5_V2 import EPD
from PIL import Image, ImageDraw, ImageFont
from constant import colors
from devices import draw_device_icons
from weather import draw_weather

epd = EPD()
epd.init()
epd.Clear()

# Image
width, height = 800, 480
image = Image.new("L", (width, height), 255)
draw = ImageDraw.Draw(image)
padding = 16

draw_device_icons(draw, (padding, padding))
draw_weather(draw, (padding + 36*3, padding))

epd.display(epd.getbuffer(image))

epd.sleep()
