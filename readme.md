# Home Control Panel (E-Ink)

A dashboard for displaying various information on an E-Ink display, designed for
a Raspberry Pi Zero W.

## Getting started

Create and activate a Python virtual environment (recommended) and install
dependencies:

```
python3 -m venv venv # once
source venv/bin/activate
pip install -r requirements.txt
```

On subsequent shells, just reactivate with:

```
source venv/bin/activate
```

Then generate the image once to verify everything works:

```
python to-image.py
```

Run `main.py` when deploying on the Raspberry Pi to update the display on an
interval.

## Icons

Material icons can be found here: https://fonts.google.com/icons

## Development

Run the following command to automatically rebuild the image when code changes:

```
\ls *.py | entr -r python to-image.py
```

### MQTT Debugging

Use `mqtt_debug.py` to inspect MQTT traffic. It highlights device topics defined
in `config.py`.

Filtering:

- `MQTT_TOPIC_PREFIX` (in `config.py`) defaults to `statechange` and makes the
  debug script subscribe to `statechange/#` instead of all topics (`#`).
- Set `MQTT_TOPIC_PREFIX = None` (or export env var `MQTT_TOPIC_PREFIX=`) to see
  everything.

Run (after activating the virtual environment):

```
python mqtt_debug.py
```

Optional overrides:

```
MQTT_HOST=192.168.1.10 MQTT_PORT=1883 MQTT_TOPIC_PREFIX=statechange python mqtt_debug.py
```

Sample output line:

```
[2025-10-26 12:34:56] TOPIC=statechange/washing_machine QOS=0 RETAIN=0 PAYLOAD=True <DEVICE label='Tvättmaskin' state=ON>
```

Boolean-like payloads (on/off/true/false/1/0) and JSON are auto-interpreted for
readability.

### Render Debounce

To avoid a burst of renders when many retained messages arrive immediately after
connecting to MQTT, rendering is debounced:

- `MQTT_RENDER_DEBOUNCE_SECONDS` (default 3) batches rapid device state changes
  so only one redraw happens after the last message in the burst.
- Applies to both `run_dev.py` (PNG mode) and `run_display.py` (E-Ink mode).
- On shutdown any pending debounced render is flushed so the final state is
  saved/displayed.

## Weather API Integration

The weather display uses OpenWeatherMap's One Call API 3.0. To use:

1. Sign up for an API key at
   [OpenWeatherMap](https://home.openweathermap.org/users/sign_up)
2. Update `config.py` with your API key and location coordinates
3. The weather data is cached for 1 hour to minimize API calls

API data is automatically fetched when the display updates, providing:

- Current temperature and weather condition
- Wind speed
- Sunrise and sunset times
- Precipitation data
- UV index with forecast for high UV periods
- 5-day weather forecast
