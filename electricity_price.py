import os
import json
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error
from PIL import Image, ImageDraw, ImageFont
from gui_constant import colors, icon_size, icon_font, text_font
from config import TIBBER_TOKEN

# Cache settings (TTL 5 hours)
ELECTRICITY_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "electricity_cache.json")
ELECTRICITY_CACHE_TTL = 18000  # 5 hours in seconds

# GraphQL query for Tibber (combined price + consumption)
TIBBER_QUERY = """
{\n  viewer {\n    homes {\n      currentSubscription {\n        priceInfo {\n          today {\n            total\n            startsAt\n            level\n          }\n          tomorrow {\n            total\n            startsAt\n            level\n          }\n        }\n      }\n      consumption(resolution: DAILY, last: 7) {\n        nodes {\n          cost\n          consumption\n        }\n      }\n    }\n  }\n}\n"""

LEVEL_LABEL_SV = {
    "NORMAL": "Normalt",
    "CHEAP": "Billigt",
    "VERY_CHEAP": "Mycket billigt",
    "EXPENSIVE": "Dyrt",
    "VERY_EXPENSIVE": "Mycket dyrt"
}


def _load_electricity_cache():
    try:
        if os.path.exists(ELECTRICITY_CACHE_FILE):
            with open(ELECTRICITY_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            if time.time() - cache.get('timestamp', 0) < ELECTRICITY_CACHE_TTL:
                return cache.get('data')
    except Exception as e:
        print(f"Error reading electricity cache: {e}")
    return None

def _save_electricity_cache(data):
    try:
        with open(ELECTRICITY_CACHE_FILE, 'w') as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        print(f"Error writing electricity cache: {e}")

def _fetch_tibber_prices():
    """Fetch raw price data from Tibber GraphQL API. Returns dict or None plus error code."""
    if not TIBBER_TOKEN:
        # No token configured
        return None, 401
    try:
        url = "https://api.tibber.com/v1-beta/gql"
        body = json.dumps({"query": TIBBER_QUERY}).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {TIBBER_TOKEN}')
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None, resp.status
            data = json.loads(resp.read().decode('utf-8'))
            return data, None
    except urllib.error.HTTPError as e:
        return None, e.code
    except urllib.error.URLError as e:
        print(f"Electricity price URL Error: {e.reason}")
        return None, None
    except Exception as e:
        print(f"Unexpected electricity fetch error: {e}")
        return None, None

def get_electricity_price_data():
    """Get processed electricity price list and consumption data.

    Returns: (prices_list, entries, highlight_index, level_label, consumption_values, consumption_costs, error_code)
    prices_list: list of int (öre)
    entries: list of dict with total_ore, startsAt, level
    highlight_index: int or -1
    level_label: Swedish label string or "" if not available
    consumption_values: list of floats (kWh) last 7 days (may be empty)
    consumption_costs: list of floats (SEK) aligned with consumption_values
    error_code: HTTP status code if failed, else None
    """
    # Try cache
    cached = _load_electricity_cache()
    error_code = None
    if cached:
        source_data = cached
    else:
        fetched, error_code = _fetch_tibber_prices()
        if fetched:
            source_data = fetched
            _save_electricity_cache(fetched)
        else:
            # If fetch failed but cache exists (already handled) else return empty
            source_data = None

    if not source_data:
        return [], [], -1, "", [], [], error_code

    try:
        homes = source_data.get('data', {}).get('viewer', {}).get('homes', [])
        if not homes:
            return [], [], -1, "", [], [], error_code
        price_info = homes[0].get('currentSubscription', {}).get('priceInfo', {})
        today = price_info.get('today', []) or []
        tomorrow = price_info.get('tomorrow', []) or []
        combined = today + tomorrow

        processed = []
        for entry in combined:
            total = entry.get('total', 0)  # Price in SEK/kWh presumably; spec says multiply by 100
            starts_at = entry.get('startsAt')
            level = entry.get('level', '')
            # Convert to öre: multiply by 100 and truncate decimals
            price_ore = int(total * 100)
            processed.append({
                'total_ore': price_ore,
                'startsAt': starts_at,
                'level': level
            })

        # Determine highlight index: entry whose startsAt <= now < next startsAt
        now = datetime.now(timezone.utc)
        highlight_index = -1
        for i, entry in enumerate(processed):
            try:
                starts = datetime.fromisoformat(entry['startsAt'].replace('Z', '+00:00'))
            except Exception:
                continue
            # Determine end boundary
            if i + 1 < len(processed):
                try:
                    next_starts = datetime.fromisoformat(processed[i+1]['startsAt'].replace('Z', '+00:00'))
                except Exception:
                    next_starts = starts
            else:
                next_starts = starts
            if starts <= now < next_starts:
                highlight_index = i
                break
        level_label = ""
        if 0 <= highlight_index < len(processed):
            level_label = LEVEL_LABEL_SV.get(processed[highlight_index]['level'], processed[highlight_index]['level'])

        prices_list = [p['total_ore'] for p in processed]
        # Extract consumption nodes from same response
        nodes = homes[0].get('consumption', {}).get('nodes', [])
        consumption_values = []
        consumption_costs = []
        for n in nodes:
            c = n.get('consumption')
            cost = n.get('cost')
            if c is not None:
                try:
                    consumption_values.append(float(c))
                except ValueError:
                    pass
            if cost is not None:
                try:
                    consumption_costs.append(float(cost))
                except ValueError:
                    pass
        return prices_list, processed, highlight_index, level_label, consumption_values, consumption_costs, error_code
    except Exception as e:
        print(f"Error processing Tibber price data: {e}")
        return [], [], -1, "", [], [], error_code

def draw_price_chart(draw, pos, width, height, prices, highlight_index):
    # Chart area dimensions
    chart_width = width  # Fixed width as requested
    chart_height = height - 30  # Leave space for padding at bottom

    # Calculate scaling factors
    if not prices:
        return  # Nothing to draw
    max_price = max(prices)
    min_price = min(prices)
    y_scaling = chart_height / (max_price - min_price) if max_price != min_price else 1
    x_scaling = chart_width / (len(prices) - 1) if len(prices) > 1 else 1

    # Draw some y-axis labels
    y_labels = [min_price, (max_price + min_price) / 2, max_price]
    for i, label in enumerate(y_labels):
        y_pos = pos[1] + chart_height - (label - min_price) * y_scaling
        draw.text((pos[0], y_pos - 6), f"{label:.0f}", font=text_font, fill=colors["black"])

    # Plot the price data
    points = []
    for i, p in enumerate(prices):
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


def draw_consumption_chart(draw, pos, width, height, consumption, costs):
    # Chart area dimensions
    chart_width = width
    chart_height = height

    # Calculate scaling factors
    if not consumption:
        return
    max_consumption = max(consumption)
    y_scaling = chart_height / max_consumption if max_consumption > 0 else 1

    # Calculate bar width based on available space and number of bars
    bar_width = int(chart_width / len(consumption)) - 4  # 4px gap between bars

    # Draw axis labels with increased spacing (moved from -20 to -30)
    draw.text((pos[0], pos[1] - 30), "Förbrukning (kWh, kr)", font=text_font, fill=colors["black"])

    # Draw some y-axis labels
    y_labels = [max_consumption / 2, max_consumption]
    for i, label in enumerate(y_labels):
        y_pos = pos[1] + chart_height - (label * y_scaling)
        draw.text((pos[0], y_pos - 6), f"{label:.1f}", font=text_font, fill=colors["black"])

    # Draw the bars
    for i, value in enumerate(consumption):
        bar_height = value * y_scaling
        x1 = pos[0] + 35 + i * (bar_width + 4)  # 4px gap
        y1 = pos[1] + chart_height - bar_height
        x2 = x1 + bar_width
        y2 = pos[1] + chart_height

        # Draw the bar
        draw.rectangle([x1, y1, x2, y2], outline=colors["black"], fill=None, width=1)

        # Draw cost underneath each bar if available
        if costs and i < len(costs):
            cost_val = costs[i]
            # Truncate to integer (floor) and show without currency suffix
            try:
                label = str(int(cost_val))
            except Exception:
                label = ""
        else:
            label = ""
        draw.text((x1 + (bar_width / 2) - 6, y2 + 5), label, font=text_font, fill=colors["dark_gray"])  # adjusted shift for shorter text


def draw_electricity_price(draw, pos):
    prices, entries, highlight_index, level_label, consumption_values, consumption_costs, error_code = get_electricity_price_data()

    title = "Elpris"
    if level_label:
        # Append current highlighted price if available
        if 0 <= highlight_index < len(prices):
            current_price = prices[highlight_index]
            title = f"{title} ({level_label} {current_price} öre)"
        else:
            title = f"{title} ({level_label})"
    draw.text((pos[0], pos[1]), title, font=text_font, fill=colors["black"])

    # Draw the price chart below the title
    price_chart_width = 240
    price_chart_height = 100
    price_chart_pos = (pos[0], pos[1] + 30)

    draw_price_chart(draw, price_chart_pos, price_chart_width, price_chart_height, prices, highlight_index)

    # If there was an error (HTTP status) show it below the price chart area
    if error_code is not None:
        error_text = f"Fel: {error_code}"
        draw.text((price_chart_pos[0], price_chart_pos[1] + price_chart_height + 5), error_text, font=text_font, fill=colors["black"])

    # Draw the consumption chart below the price chart (adjust y if error shown)
    consumption_chart_width = 240
    consumption_chart_height = 80
    gap = 40
    extra_offset = 20 if error_code is not None else 0
    consumption_chart_pos = (pos[0], pos[1] + 30 + price_chart_height + gap + extra_offset)

    draw_consumption_chart(draw, consumption_chart_pos, consumption_chart_width, consumption_chart_height, consumption_values, consumption_costs)
