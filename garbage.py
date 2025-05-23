from PIL import Image, ImageDraw, ImageFont
from constant import colors, icon_size, icon_font, text_font, text_size
from datetime import datetime, timedelta

# Fake garbage collection data
# This could later be fetched from an external source
# Each tuple contains (household waste date, garden waste date)
# Both dates are in the same week, Wednesday and Friday
garbage_collection_dates = [
    {"household": "2025-05-28", "garden": "2025-05-30"},  # Week 1
    {"household": "2025-06-11", "garden": "2025-06-13"},  # Week 3
    {"household": "2025-06-25", "garden": "2025-06-27"},  # Week 5
    {"household": "2025-07-09", "garden": "2025-07-11"},  # Week 7
    {"household": "2025-07-23", "garden": "2025-07-25"},  # Week 9
]

def get_next_collection(date_str):
    """Find the next garbage collection dates after the given date."""
    today = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Filter dates that are in the future
    future_dates = []
    for collection in garbage_collection_dates:
        household_date = datetime.strptime(collection["household"], "%Y-%m-%d").date()
        garden_date = datetime.strptime(collection["garden"], "%Y-%m-%d").date()

        if household_date >= today:
            future_dates.append({"type": "household", "date": household_date})
        if garden_date >= today:
            future_dates.append({"type": "garden", "date": garden_date})

    # Sort by date
    future_dates.sort(key=lambda x: x["date"])

    # Return next 2 collections or fewer if not enough future dates
    return future_dates[:2]

def get_days_until(target_date, today_str):
    """Calculate days until the target date from today."""
    today = datetime.strptime(today_str, "%Y-%m-%d").date()
    days = (target_date - today).days

    if days == 0:
        return "idag"
    elif days == 1:
        return "imorgon"
    else:
        return f"om {days} dagar"

def get_reminder_message(collection, today_str):
    """Generate a reminder message in Swedish based on collection type and date."""
    days_until = get_days_until(collection["date"], today_str)
    date_str = collection["date"].strftime("%d/%m")

    if collection["type"] == "household":
        return f"Hushållssopor: {date_str} ({days_until})"
    else:
        return f"Trädgårdsavfall: {date_str} ({days_until})"

def draw_garbage_collection(draw, pos, today_str="2025-05-29"):
    """Draw the garbage collection information section."""
    # Draw trash icon to the left of the title
    # draw.text((pos[0], pos[1]), "\ue872", font=icon_font, fill=colors["black"])

    # Draw section title after the icon
    icon_width = icon_size + 8  # Icon width plus some spacing
    # draw.text((pos[0] + icon_width, pos[1] + (icon_size - text_size) / 2), "Sophämtning", font=text_font, fill=colors["black"])

    # Get the next collections
    next_collections = get_next_collection(today_str)

    # Calculate positions and spacing
    title_height = text_size + 12
    line_height = text_size + 8
    start_y = pos[1] + title_height

    # Draw reminders for the next collections
    for i, collection in enumerate(next_collections):
        reminder_y = start_y + line_height * i  # Adjusted to start immediately after title
        reminder_text = get_reminder_message(collection, today_str)
        draw.text((pos[0], reminder_y), reminder_text, font=text_font, fill=colors["black"])

    # Add a general instruction if next collection is soon (within 2 days)
    if next_collections and get_days_until(next_collections[0]["date"], today_str) in ["idag", "imorgon"]:
        instruction_y = start_y + line_height * len(next_collections)  # Adjusted to follow the collection items directly
        type_text = "Hushållssoporna" if next_collections[0]["type"] == "household" else "Trädgårdsavfallet"
        draw.text((pos[0], instruction_y), f"Dags att ställa ut {type_text.lower()}!",
                font=text_font, fill=colors["black"])
