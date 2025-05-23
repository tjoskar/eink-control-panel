import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from config import (
    WEATHER_API_KEY,
    WEATHER_LAT,
    WEATHER_LON,
    WEATHER_UNITS,
    WEATHER_LANG,
    API_TIMEOUT,
    CACHE_DURATION
)

# File path for cached weather data
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_cache.json")

# Weather icons mapping from OpenWeatherMap codes to icon font characters
# This mapping may need to be adjusted based on the specific icons in your font
WEATHER_ICONS = {
    # Clear
    "01d": "\uf157",  # Clear day
    "01n": "\ue386",  # Clear night
    # Partly cloudy
    "02d": "\ue81a",  # Few clouds day
    "02n": "\ue391",  # Few clouds night
    # Cloudy
    "03d": "\ue818",  # Scattered clouds
    "03n": "\ue818",
    "04d": "\ue818",  # Broken clouds
    "04n": "\ue818",
    # Rain
    "09d": "\ue798",  # Shower rain
    "09n": "\ue798",
    "10d": "\ue7d0",  # Rain day
    "10n": "\ue7d0",  # Rain night
    # Thunderstorm
    "11d": "\ue80f",  # Thunderstorm
    "11n": "\ue80f",
    # Snow
    "13d": "\ue80c",  # Snow
    "13n": "\ue80c",
    # Mist/fog
    "50d": "\ue8e7",  # Mist
    "50n": "\ue8e7"
}

# Day of week abbreviations in Swedish
DAYS_OF_WEEK_SV = {
    0: "Mån",
    1: "Tis",
    2: "Ons",
    3: "Tor",
    4: "Fre",
    5: "Lör",
    6: "Sön"
}

def get_cached_data():
    """Get weather data from cache file if it exists and is not expired."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            if time.time() - cache_data.get('timestamp', 0) < CACHE_DURATION:
                return cache_data.get('data')
    except Exception as e:
        print(f"Error reading cache: {e}")
    return None

def save_to_cache(data):
    """Save weather data to cache file."""
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Error writing cache: {e}")

def fetch_weather_data():
    """Fetch weather data from OpenWeatherMap API or cache."""

    # Check cache first
    cached_data = get_cached_data()
    if cached_data:
        return cached_data

    # If no valid cache, make API request
    try:
        url = (f"https://api.openweathermap.org/data/3.0/onecall"
               f"?lat={WEATHER_LAT}&lon={WEATHER_LON}"
               f"&units={WEATHER_UNITS}&lang={WEATHER_LANG}"
               f"&appid={WEATHER_API_KEY}")

        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=API_TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))

            # Save to cache
            save_to_cache(data)
            return data

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        if e.code == 401:
            print("Invalid API key - check your API key in config.py")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"Error fetching weather data: {e}")

    # Return fallback data in case of an error
    return get_fallback_data()

def get_fallback_data():
    """Generate fallback weather data in case of API failure."""
    return {
        "current": {
            "temp": 15.0,
            "weather": [{"icon": "01d"}],
            "wind_speed": 5.0,
            "sunrise": int(time.time()),
            "sunset": int(time.time()) + 43200,  # +12 hours
            "rain": {"1h": 0},
            "uvi": 1.0
        },
        "daily": [
            {
                "dt": time.time() + i * 86400,
                "temp": {"min": 10.0, "max": 20.0},
                "weather": [{"icon": "01d"}]
            } for i in range(5)
        ]
    }

def get_uv_info(weather_data):
    """Extract UV index information."""
    current_uv = weather_data.get('current', {}).get('uvi', 0)

    # Find max UV for the day
    max_uv = current_uv
    hours_above_3 = []

    hourly = weather_data.get('hourly', [])
    for i, hour in enumerate(hourly):
        uv = hour.get('uvi', 0)
        if uv > max_uv:
            max_uv = uv

        # Track hours where UV > 3 (moderate or higher)
        if uv > 3:
            hour_time = datetime.fromtimestamp(hour.get('dt', 0))
            hours_above_3.append(hour_time.hour)

    # Format the hours with high UV into ranges
    uv_ranges = []
    if hours_above_3:
        start = hours_above_3[0]
        end = start

        for i in range(1, len(hours_above_3)):
            if hours_above_3[i] == end + 1:
                end = hours_above_3[i]
            else:
                if start == end:
                    uv_ranges.append(f"{start}")
                else:
                    uv_ranges.append(f"{start} - {end}")
                start = hours_above_3[i]
                end = start

        # Add the last range
        if start == end:
            uv_ranges.append(f"{start}")
        else:
            uv_ranges.append(f"{start} - {end}")

    # Format UV information
    if not uv_ranges:
        uv_text = f"{current_uv:.0f} ({max_uv:.0f})"
    else:
        uv_text = f"{current_uv:.0f} ({max_uv:.0f}, {', '.join(uv_ranges)})"

    return uv_text

def get_weather_display_data():
    """Process weather data into the format needed for display."""
    try:
        weather_data = fetch_weather_data()

        # Current weather data
        current = weather_data.get('current', {})
        temp = current.get('temp', 0)
        weather_icon = current.get('weather', [{}])[0].get('icon', '01d')
        wind_speed = current.get('wind_speed', 0)

        # Sunrise/sunset times
        sunrise_time = datetime.fromtimestamp(current.get('sunrise', 0))
        sunset_time = datetime.fromtimestamp(current.get('sunset', 0))
        sun_times = f"{sunrise_time.strftime('%H:%M')} / {sunset_time.strftime('%H:%M')}"

        # Precipitation data
        rain_1h = current.get('rain', {}).get('1h', 0) if current.get('rain') else 0

        # UV index information
        uv_info = get_uv_info(weather_data)

        # Daily forecast data
        forecast = []
        for i, day in enumerate(weather_data.get('daily', [])[:5]):  # Get 5-day forecast
            day_dt = datetime.fromtimestamp(day.get('dt', 0))
            day_name = DAYS_OF_WEEK_SV.get(day_dt.weekday(), "")

            day_icon_code = day.get('weather', [{}])[0].get('icon', '01d')
            day_icon = WEATHER_ICONS.get(day_icon_code, "\ue818")  # Default to cloudy if icon not found

            temp_min = day.get('temp', {}).get('min', 0)
            temp_max = day.get('temp', {}).get('max', 0)
            temp_text = f"{temp_min:.0f}°/{temp_max:.0f}°"

            forecast.append({
                "day": day_name,
                "icon": day_icon,
                "temp": temp_text
            })

        return {
            "current": {
                "temp": f"{temp:.0f}°",
                "icon": WEATHER_ICONS.get(weather_icon, "\ue818"),
                "wind_speed": f"{wind_speed:.0f} m/s",
                "sun_times": sun_times,
                "rain": f"{rain_1h:.1f} mm",
                "uv_info": uv_info
            },
            "forecast": forecast
        }
    except Exception as e:
        print(f"Error processing weather data: {e}")
        # Return fallback display data
        return {
            "current": {
                "temp": "15°",
                "icon": "\uf157",
                "wind_speed": "5 m/s",
                "sun_times": "06:18 / 21:05",
                "rain": "0 mm",
                "uv_info": "1 (3, 10 - 14)"
            },
            "forecast": [
                {"day": "Mån", "icon": "\uf157", "temp": "16°/24°"},
                {"day": "Tis", "icon": "\ue81a", "temp": "14°/20°"},
                {"day": "Ons", "icon": "\ue798", "temp": "10°/17°"},
                {"day": "Tor", "icon": "\ue818", "temp": "12°/19°"},
                {"day": "Fre", "icon": "\ue80f", "temp": "15°/22°"}
            ]
        }

if __name__ == "__main__":
    # Test the module if run directly
    data = get_weather_display_data()
    print("Current Weather:")
    print(f"Temperature: {data['current']['temp']}")
    print(f"Icon: {data['current']['icon']}")
    print(f"Wind Speed: {data['current']['wind_speed']}")
    print(f"Sun Times: {data['current']['sun_times']}")
    print(f"Rain: {data['current']['rain']}")
    print(f"UV Info: {data['current']['uv_info']}")
    print("\nForecast:")
    for day in data['forecast']:
        print(f"{day['day']}: {day['icon']} {day['temp']}")
