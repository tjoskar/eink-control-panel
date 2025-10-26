from PIL import Image, ImageDraw, ImageFont
from gui_constant import colors, icon_size, icon_font, text_font

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

consumption = [
  2.42,
  1.45,
  2.15,
  1.19,
  1.23,
  2.23,
  2.12
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

    # Draw step chart with vertical lines between points
    if len(points) > 1:
        for i in range(len(points) - 1):
            # Draw horizontal line from current point to below the next point
            draw.line([(points[i][0], points[i][1]), (points[i+1][0], points[i][1])],
                      fill=colors["black"], width=2)

            # Draw vertical line from below the next point to the next point
            draw.line([(points[i+1][0], points[i][1]), (points[i+1][0], points[i+1][1])],
                      fill=colors["black"], width=2)

    # Only draw dot at highlight_index
    if 0 <= highlight_index < len(points):
        highlight_point = points[highlight_index]
        draw.ellipse((highlight_point[0] - 3, highlight_point[1] - 3,
                      highlight_point[0] + 3, highlight_point[1] + 3),
                     fill=colors["black"])


def draw_consumption_chart(draw, pos, width, height):
    # Chart area dimensions
    chart_width = width
    chart_height = height

    # Calculate scaling factors
    max_consumption = max(consumption)
    y_scaling = chart_height / max_consumption if max_consumption > 0 else 1

    # Calculate bar width based on available space and number of bars
    bar_width = int(chart_width / len(consumption)) - 4  # 4px gap between bars

    # Draw axis labels with increased spacing (moved from -20 to -30)
    draw.text((pos[0], pos[1] - 30), "Förbrukning (kWh)", font=text_font, fill=colors["black"])

    # Draw some y-axis labels
    y_labels = [max_consumption / 2, max_consumption]
    for i, label in enumerate(y_labels):
        y_pos = pos[1] + chart_height - (label * y_scaling)
        draw.text((pos[0], y_pos - 6), f"{label:.1f}", font=text_font, fill=colors["black"])
        draw.line([(pos[0] + 25, y_pos), (pos[0] + 30, y_pos)], fill=colors["black"], width=1)  # tick mark

    # Draw the bars
    for i, value in enumerate(consumption):
        bar_height = value * y_scaling
        x1 = pos[0] + 30 + i * (bar_width + 4)  # 4px gap
        y1 = pos[1] + chart_height - bar_height
        x2 = x1 + bar_width
        y2 = pos[1] + chart_height

        # Draw the bar
        draw.rectangle([x1, y1, x2, y2], outline=colors["black"], fill=None, width=1)

        # Optional: Draw day number underneath each bar
        # draw.text((x1 + (bar_width / 2) - 4, y2 + 5), str(i+1), font=text_font, fill=colors["black"])


def draw_electricity_price(draw, pos):
    draw.text((pos[0], pos[1]), "Elpris", font=text_font, fill=colors["black"])

    # Draw the price chart below the title
    price_chart_width = 240
    price_chart_height = 100
    price_chart_pos = (pos[0], pos[1] + 30)

    draw_price_chart(draw, price_chart_pos, price_chart_width, price_chart_height)

    # Draw the consumption chart below the price chart
    consumption_chart_width = 240
    consumption_chart_height = 80
    consumption_chart_pos = (pos[0], pos[1] + 30 + price_chart_height + 40)  # 40px gap between charts

    draw_consumption_chart(draw, consumption_chart_pos, consumption_chart_width, consumption_chart_height)
