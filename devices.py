from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font

# Device data
devices = [
    {"label": "Dishwasher", "icon": "\uefef", "on": True},
    {"label": "Washing Machine", "icon": "\ue832", "on": True},
    {"label": "Tumble Dryer", "icon": "\ue54a", "on": False},
    {"label": "Lawn Mower", "icon": "\uf089", "on": False},
    {"label": "Bike Charger", "icon": "\ueb1b", "on": True},
    {"label": "Outdoor Lights", "icon": "\ue28b", "on": False},
    {"label": "Window Lights", "icon": "\ue90f", "on": True},
]


def draw_device_icons(draw, pos):
  # Layout
  box_padding = 4
  box_height = icon_size + box_padding * 2

  icon_y_offset = pos[1]
  for device in devices:
      y = icon_y_offset
      # draw.rectangle([padding, y, padding + icon_size, y + box_height], outline=0)

      if device["on"]:
          icon_color = colors["black"]
      else:
          icon_color = colors["light_gray"]

      draw.text((pos[0], y), device["icon"], font=icon_font, fill=icon_color)
      # if device["label"] == "Washing Machine":
        # draw.text((padding + icon_size + 4, y + 4), device["label"], font=text_font, fill=0)
        # draw.text((pos[0] + icon_size + 4, y + 4), "1 timme kvar", font=text_font, fill=0)

      icon_y_offset += box_height
