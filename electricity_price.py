from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font

# Device data
price = [
    41.73,
    40.28,
    35.40,
    30.38,
    30.84,
    39.14,
    43.84,
    45.77,
    36.50,
    32.98,
    23.02,
    7.39,
    4.56,
    4.07,
    3.35,
    4.91,
    9.42,
    28.20,
    43.08,
    50.38,
    40.46,
    40.21,
    39.54,
    28.43,
]


def draw_price_chart(draw, pos, width, height):
    highlight_index = 13
    # Chart area dimensions
    chart_width = width  # Fixed width as requested
    chart_height = height - 30  # Leave space for padding at bottom

    # Calculate scaling factors
    max_price = max(price)
    min_price = min(price)
    y_scaling = chart_height / (max_price - min_price) if max_price != min_price else 1
    x_scaling = chart_width / (len(price) - 1) if len(price) > 1 else 1

    # Draw axes
    # draw.line([(pos[0] + 30, pos[1]), (pos[0] + 30, pos[1] + chart_height)], fill=colors["black"], width=1)  # y-axis
    # draw.line([(pos[0] + 30, pos[1] + chart_height), (pos[0] + 30 + chart_width, pos[1] + chart_height)], fill=colors["black"], width=1)  # x-axis

    # Draw some y-axis labels
    y_labels = [min_price, (max_price + min_price) / 2, max_price]
    for i, label in enumerate(y_labels):
        y_pos = pos[1] + chart_height - (label - min_price) * y_scaling
        draw.text((pos[0], y_pos - 6), f"{label:.0f}", font=text_font, fill=colors["black"])
        draw.line([(pos[0] + 25, y_pos), (pos[0] + 30, y_pos)], fill=colors["black"], width=1)  # tick mark

    # Plot the price data
    points = []
    for i, p in enumerate(price):
        x = pos[0] + 30 + i * x_scaling
        y = pos[1] + chart_height - (p - min_price) * y_scaling
        points.append((x, y))

    # Draw the line connecting all points
    if len(points) > 1:
        draw.line(points, fill=colors["black"], width=2)

    # Only draw dot at highlight_index
    if 0 <= highlight_index < len(points):
        highlight_point = points[highlight_index]
        draw.ellipse((highlight_point[0] - 3, highlight_point[1] - 3,
                      highlight_point[0] + 3, highlight_point[1] + 3),
                     fill=colors["black"])


def draw_electricity_price(draw, pos):
    draw.text((pos[0], pos[1]), "El pris", font=text_font, fill=colors["black"])

    # Draw the price chart below the title
    chart_width = 240  # Adjust based on your display needs
    chart_height = 100  # Adjust based on your display needs
    chart_pos = (pos[0], pos[1] + 30)  # Position below the title

    draw_price_chart(draw, chart_pos, chart_width, chart_height)
