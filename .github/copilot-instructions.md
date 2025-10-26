# AI Coding Agent Guide: E-Ink Home Control Panel

> Goal: Show information from smart home devices on an E-Ink dashboard (800x480) Waveshare HW (EPD 7.5 V2). Rendered via Pillow (PIL) on Raspberry Pi Zero W.

## Big Picture
- Image composition = a blank `Image.new("L", (800, 480), 255)` + sequential `draw_<section>()` calls placing content via manual x,y offsets.
- Use as few dependencies as possible.
- Remember: This runs on a Raspberry Pi Zero W with limited CPU/RAM!
- The output is in Swedish but all code/comments should remain in English.
- Two usage modes:
  - Local preview: `venv/bin/python to_image.py` -> writes `main.png` (always use the virtualenv interpreter).
  - Hardware display: `venv/bin/python to_display.py` (Waveshare driver `lib/waveshare_epd/epd7in5_V2.py`).

## Key Files & Responsibilities
- `compose.py`: Single source for panel layout; `compose_panel(devices)` returns a PIL Image with all sections drawn.
- `to_image.py`: Thin wrapper calling `compose_panel` then saving `main.png`.
- `to_display.py`: Thin wrapper calling `compose_panel` then pushing to Waveshare EPD (clear + display + sleep).
- `run_dev.py`: Long‑running PNG mode (MQTT + periodic refresh via `REFRESH_INTERVAL`).
- `run_display.py`: Long‑running E‑Ink mode (hardware init + MQTT + periodic refresh).
- `mqtt_listener.py`: Legacy simple listener (can be replaced by runners above).
- `weather_api.py`: Fetch + 1h file cache (`weather_cache.json`), fallback data, icon mapping, UV range derivation.
- `weather.py`: Rendering logic for current + 5‑day forecast (Swedish localization) using layout constants & font metrics.
- `electricity_price.py`: Step chart (prices) + bar chart (consumption). Pattern for drawing a titled mini-chart.
- `devices.py`: Global in‑memory `DEVICES` list + update helpers; icon grayscale indicates on/off.
- `garbage.py` / `dishes.py`: Text list sections with Swedish phrasing.
- `constant.py`: Central fonts + grayscale palette; treat as the single source of visual style.
- `config.py`: Weather API parameters, cache settings, `REFRESH_INTERVAL`.

## Development Workflow
- Create & activate venv; install deps: Pillow + paho-mqtt.
- Fast iterate preview: `\ls *.py | entr -r venv/bin/python to_image.py`.
- Continuous dev run: `venv/bin/python run_dev.py` (auto refresh + MQTT).
- Continuous hardware run: `venv/bin/python run_display.py` (auto refresh + MQTT + E-Ink push).
- For quick one-off MQTT test: legacy `mqtt_listener.py` still works.
- Text centering: `draw.textbbox` width calc (see `get_text_width` in `weather.py`, `dishes.py`). Reuse, don’t reimplement with font.getsize.
## Caching & Network
- Weather cache TTL = `CACHE_DURATION` (seconds). Honor existing file path logic; if extending, keep atomic JSON writes.
- On failure: `get_fallback_data()` returns deterministic stub—preserve this safety net.
- Periodic redraw interval controlled by `REFRESH_INTERVAL` in `config.py` (used by runner scripts).
- Avoid adding per-call font loads; reuse global font objects defined in `constant.py`.

## Weather Data Shape (from `get_weather_display_data()`)
```
{
  current: {temp: "15°", icon: <glyph>, wind_speed: "5 m/s", sun_times: "06:18 / 21:05", rain: "0 mm", uv_info: "1 (3, 10 - 14)"},
  forecast: [{day: "Mån", icon: <glyph>, temp: "16°/24°"}, ... up to 5]
}
```
Use this directly—do NOT refetch inside a renderer.

## Caching & Network
- Weather cache TTL = `CACHE_DURATION` (seconds). Honor existing file path logic; if extending, keep atomic JSON writes.
- On failure: `get_fallback_data()` returns deterministic stub—preserve this safety net.

## Fonts & Icons
- Glyphs derive from custom font files in `fonts/` (`1.woff`, `noto-sans-regular.ttf`). Avoid adding new font loads per frame; reuse existing globals.
- Icon codes mapped in `WEATHER_ICONS`; add new codes there if needed (fallback defaults to cloudy glyph).

## Adding a New Section (Example Template)
```python
# my_section.py
from constant import colors, text_font

def draw_my_section(draw, pos):
    draw.text((pos[0], pos[1]), "Titel", font=text_font, fill=colors["black"])
    # further drawing...
```
Then integrate inside `compose_panel` in `compose.py` (single source of layout). Do NOT add drawing logic directly to output scripts.

## Development Workflow
- Create & activate venv; install deps: Pillow + paho-mqtt.
- Fast iterate preview: `\ls *.py | entr -r venv/bin/python to_image.py`.
- Dynamic device updates: run `venv/bin/python mqtt_listener.py` then publish MQTT messages.
- Hardware: adapt `to-disply.py` only for EPD init/clear/display/sleep; keep layout untouched.

## Data & Localization
- Swedish abbreviations & phrases (e.g., "Hushållssopor", "Veckans mat"). Maintain consistency; if translating, update all modules.
- Hardcoded demo arrays (prices, consumption, dishes, garbage dates) are placeholders—if replaced with real sources, preserve function signatures.

## Safety / Do Not
- Don’t embed or print the API key outside `config.py`.
- Don’t introduce non-grayscale colors (display is mono).
- Don’t refactor into class-based architecture unless a clear multi-frame or stateful need arises.
- Don’t break existing positional assumptions without updating all call sites.

## Good Extension Targets
- Replace stubs with live data providers (electricity API, calendar/ICS feed for dishes/garbage, device states from MQTT topics).
- Add bounding-box collision check (script comparing `draw.textbbox` outputs) before pushing to hardware.
- Consider separating data acquisition from render (future: precompute JSON -> render only on Pi for speed).
- Consolidate fonts if memory pressure arises; test glyph coverage first.
- REMEMBER: Pi Zero W is resource constrained—avoid heavy libs (keep numpy/pandas out).

---
Questions or missing conventions? Ask for clarification before large refactors.
