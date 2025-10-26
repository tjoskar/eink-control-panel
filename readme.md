# Home Control Panel (E-Ink)

A dashboard for displaying various information on an E-Ink display, designed for a Raspberry Pi Zero W.

## Getting started

Create and activate a Python virtual environment (recommended) and install dependencies:

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

Run `main.py` when deploying on the Raspberry Pi to update the display on an interval.

## Icons
Material icons can be found here: https://fonts.google.com/icons

## Development
Run the following command to automatically rebuild the image when code changes:
```
\ls *.py | entr -r python to-image.py
```

## Weather API Integration
The weather display uses OpenWeatherMap's One Call API 3.0. To use:

1. Sign up for an API key at [OpenWeatherMap](https://home.openweathermap.org/users/sign_up)
2. Update `config.py` with your API key and location coordinates
3. The weather data is cached for 1 hour to minimize API calls

API data is automatically fetched when the display updates, providing:
- Current temperature and weather condition
- Wind speed
- Sunrise and sunset times
- Precipitation data
- UV index with forecast for high UV periods
- 5-day weather forecast
