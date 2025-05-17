from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font, big_icon_font, big_icon_size, headline_text_font, headline_text_size, text_size


def draw_weather(draw, pos):
  draw.text((pos[0], pos[1] + 16), "\uf157", font=big_icon_font, fill=colors["black"])
  draw.text((pos[0] + big_icon_size + 8 * 2, pos[1] + 16 + (big_icon_size - headline_text_size) / 2), "5°", font=headline_text_font, fill=colors["black"])

  detail_pos = (pos[0] + big_icon_size + headline_text_size + 8 * 4, pos[1] + 8)
  draw.text(detail_pos, "\uefd8", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + (icon_size - text_size) / 2 ), "5 m/s", font=text_font, fill=colors["black"])

  draw.text((detail_pos[0], detail_pos[1] + icon_size), "\ue1c6", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size + (icon_size - text_size) / 2 ), "06:18 / 21:05", font=text_font, fill=colors["black"])

  draw.text((detail_pos[0], detail_pos[1] + icon_size * 2), "\ue798", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size * 2 + (icon_size - text_size) / 2 ), "0 mm", font=text_font, fill=colors["black"])

  draw.text((detail_pos[0], detail_pos[1] + icon_size * 3), "\ue81a", font=icon_font, fill=colors["black"])
  draw.text((detail_pos[0] + icon_size + 8, detail_pos[1] + icon_size * 3 + (icon_size - text_size) / 2 ), "1 (3, 10 - 14)", font=text_font, fill=colors["black"])
