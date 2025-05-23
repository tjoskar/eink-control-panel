from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font, big_icon_font, big_icon_size, headline_text_font, headline_text_size, text_size
from weather_api import get_weather_display_data

def draw_weather(draw, pos):
  # Get the latest weather data from API
  weather_data = get_weather_display_data()
  current = weather_data["current"]
  forecast_data = weather_data["forecast"]

  # Current weather represented by a big icon and temperature
  draw.text((pos[0], pos[1] + 16), current["icon"], font=big_icon_font, fill=colors["black"])
  draw.text((pos[0] + big_icon_size + 8 * 2, pos[1] + 16 + (big_icon_size - headline_text_size) / 2), current["temp"], font=headline_text_font, fill=colors["black"])

  detail_pos = (pos[0] + big_icon_size + headline_text_size + 8 * 4, pos[1] + 8)

  # Current wind speed
  draw.text(detail_pos, "\uefd8", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + (icon_size - text_size) / 2 ), current["wind_speed"], font=text_font, fill=colors["black"])

  # Sunrise and sunset times for today
  draw.text((detail_pos[0], detail_pos[1] + icon_size), "\ue1c6", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size + (icon_size - text_size) / 2 ), current["sun_times"], font=text_font, fill=colors["black"])

  # Humidity/Rain
  draw.text((detail_pos[0], detail_pos[1] + icon_size * 2), "\ue798", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size * 2 + (icon_size - text_size) / 2 ), current["rain"], font=text_font, fill=colors["black"])

  # UV index, rendered "<current UV index> (<max>, <higher than 3 hours>)"
  draw.text((detail_pos[0], detail_pos[1] + icon_size * 3), "\ue81a", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size * 3 + (icon_size - text_size) / 2 ), current["uv_info"], font=text_font, fill=colors["black"])

  forecast_pos = (pos[0], big_icon_size + 8 * 2 + 8 * 8)

  # Render forecast items horizontally
  current_x = forecast_pos[0]
  for item in forecast_data:
    # Calculate temperature text width for centering the icon
    temp_width = get_text_width(draw, item["temp"], text_font)

    # Draw day name (centered relative to temperature text)
    day_width = get_text_width(draw, item["day"], text_font)
    day_x = current_x + (temp_width - day_width) / 2
    draw.text((day_x, forecast_pos[1]), item["day"], font=text_font, fill=colors["black"])

    # Draw icon (centered relative to temperature text)
    icon_x = current_x + (temp_width - icon_size) / 2
    draw.text((icon_x, forecast_pos[1] + text_size + 8), item["icon"], font=icon_font, fill=colors["black"])

    # Draw temperature
    draw.text((current_x, forecast_pos[1] + text_size + 8 + icon_size + 8), item["temp"], font=text_font, fill=colors["black"])

    # Move to the next item position
    current_x += max(temp_width, icon_size, get_text_width(draw, item["day"], text_font)) + 16


def get_text_width(draw, text, font):
  bbox = draw.textbbox((0, 0), text, font=font)
  return bbox[2] - bbox[0]
