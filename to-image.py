from PIL import Image, ImageDraw, ImageFont
from constant import colors
from devices import draw_device_icons
from weather import draw_weather
from electricity_price import draw_electricity_price

# Image
width, height = 800, 480
image = Image.new("L", (width, height), 255)
draw = ImageDraw.Draw(image)
padding = 16

draw_device_icons(draw, (padding, padding))
draw_weather(draw, (padding + 36*3, padding))
draw_electricity_price(draw, (padding + 500, padding))

# Save PNG (for testing on Mac)
image.save("main.png")

# # --- Data ---
# historik = [1, 1, 0, 0, -1, -1, -1, 0, 1, 2, 5, 6, 7, 9, 10, 12]
# prognos  = [13, 12, 10, 7, 6, 5, 4, 3]

# # --- Skapa huvudbild ---
# main_width = 800
# main_height = 480

# main_image = Image.new('1', (main_width, main_height), 255)
# draw = ImageDraw.Draw(main_image)

# draw.line((50, 50, 250, 200), fill=1, width=2)


# # --- Inställningar för grafen ---
# graph_x = 50   # vänster position på huvudbilden
# graph_y = 50   # topposition på huvudbilden
# graph_width = 200
# graph_height = 150
# margin = 20  # plats för axlar

# total_points = len(historik) + len(prognos)
# max_temp = max(historik + prognos)
# min_temp = min(historik + prognos)

# # Skala temperatur till y-pixel
# def temp_to_y(temp):
#     return graph_y + margin + graph_height - ((temp - min_temp) / (max_temp - min_temp)) * graph_height

# # Skala tid till x-pixel
# def time_to_x(index):
#     return graph_x + margin + (index / (total_points - 1)) * (graph_width - margin)

# # --- Rita axlar på huvudbilden ---
# # Y-axel
# draw.line((graph_x + margin, graph_y + margin, graph_x + margin, graph_y + graph_height), fill=0, width=1)
# # X-axel
# draw.line((graph_x + margin, graph_y + graph_height, graph_x + graph_width, graph_y + graph_height), fill=0, width=1)

# # --- Rita historik (streckad linje) ---
# for i in range(len(historik) - 1):
#     x1 = time_to_x(i)
#     y1 = temp_to_y(historik[i])
#     x2 = time_to_x(i + 1)
#     y2 = temp_to_y(historik[i + 1])

#     steps = 10
#     for s in range(steps):
#         start_x = x1 + (x2 - x1) * (s / steps)
#         start_y = y1 + (y2 - y1) * (s / steps)
#         end_x = x1 + (x2 - x1) * ((s + 0.5) / steps)
#         end_y = y1 + (y2 - y1) * ((s + 0.5) / steps)
#         draw.line((start_x, start_y, end_x, end_y), fill=200, width=1)  # ljusgrå streck

# # --- Rita prognos (hel linje) ---
# offset = len(historik)
# for i in range(len(prognos) - 1):
#     x1 = time_to_x(offset + i)
#     y1 = temp_to_y(prognos[i])
#     x2 = time_to_x(offset + i + 1)
#     y2 = temp_to_y(prognos[i + 1])

#     draw.line((x1, y1, x2, y2), fill=50, width=2)  # mörkare hel linje

# # --- Spara / visa huvudbilden ---
# main_image.save("main_graph.png")
# # eller visa direkt (om du kör på Mac!)
# # main_image.show()
