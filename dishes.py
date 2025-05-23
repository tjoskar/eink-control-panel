from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font, text_size

# Fake weekly dishes data in Swedish
# This could later be fetched from an external source
weekly_dishes = [
    {"day": "Mån", "dish": "Köttbullar med potatismos"},
    {"day": "Tis", "dish": "Pasta Carbonara"},
    {"day": "Ons", "dish": "Laxfilé med romsås"},
    {"day": "Tor", "dish": "Vegetarisk lasagne"},
    {"day": "Fre", "dish": "Tacos"},
    {"day": "Lör", "dish": "Grillad kyckling med sallad"},
]

def draw_weekly_dishes(draw, pos):
    # Draw section title
    draw.text((pos[0], pos[1]), "Veckans mat", font=text_font, fill=colors["black"])

    # Calculate positions and spacing
    title_height = text_size + 8
    dish_height = text_size + 4
    start_y = pos[1] + title_height

    # Draw each dish
    for i, item in enumerate(weekly_dishes):
        dish_y = start_y + i * dish_height

        # Draw dish name directly (without the day prefix)
        draw.text((pos[0], dish_y), "- " + item["dish"], font=text_font, fill=colors["black"])

def get_text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]
