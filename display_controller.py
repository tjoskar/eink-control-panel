"""DisplayController encapsulates E-Ink hardware rendering logic.

Responsibilities:
- Full-screen render (compose + display).
- Debounced full render scheduling.
- Partial region update (caller supplies Image + bbox).

Note: Keep this lean; Pi Zero W has limited resources.
"""

import threading
from typing import Optional, Tuple
from config import MQTT_RENDER_DEBOUNCE_SECONDS
from compose import compose_panel
from lib.waveshare_epd.epd7in5_V2 import EPD


class DisplayController:

    def __init__(self):
        # Hardware instance right away (allows early capability checks)
        self._epd = EPD()
        self._render_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._render_timer = None  # optional debounce timer
        self._render_count = 0
        print("[DISPLAY] Controller constructed")

    def stop(self):
        self._stop_event.set()
        try:
            if self._render_timer is not None:
                self._render_timer.cancel()
        except Exception:
            pass
        print("[DISPLAY] Controller stopped")

    # ---- Rendering ----
    def render(self):
        """Full panel render: init -> display -> sleep."""
        with self._render_lock:
            # Every 4th render: do a clear after init to reduce ghosting
            self._epd.init()
            do_clear = (self._render_count % 4 == 0)
            if do_clear:
                self._epd.Clear()
            img = compose_panel()
            self._epd.display(self._epd.getbuffer(img))
            self._epd.sleep()
            self._render_count += 1
            print(f"[RENDER] Full update done (count={self._render_count}, clear={do_clear})")

    def schedule_render(self):
        """Debounce display rendering to batch rapid retained messages."""
        if self._render_timer is not None:
            self._render_timer.cancel()

        def _do():
            self.render()

        self._render_timer = threading.Timer(MQTT_RENDER_DEBOUNCE_SECONDS, _do)
        self._render_timer.daemon = True
        self._render_timer.start()
        print(f"[DEBOUNCE] Display render scheduled in {MQTT_RENDER_DEBOUNCE_SECONDS}s")

    # ---- Helpers ----
    @property
    def stopped(self) -> bool:
        return self._stop_event.is_set()

    # ---- Partial update ----
    def partial_update(self, region_image, bbox: Tuple[int, int, int, int]):
        """Update only the region defined by bbox=(x1,y1,x2,y2) using a pre-cropped image.

        Caller supplies a PIL Image whose size matches (bbox_width, bbox_height).
        This avoids allocating a full-size canvas + cropping every time.
        """
        with self._render_lock:
            # Every 5th update: fall back to full render with clear
            if self._render_count % 5 == 0:
                print("[PARTIAL] Forcing full render instead (ghosting mitigation)")
                self.render()
                return
            self._epd.init_part()
            x1, y1, x2, y2 = bbox
            expected_w = x2 - x1
            expected_h = y2 - y1
            if region_image.size != (expected_w, expected_h):
                print(f"[PARTIAL] Region image size {region_image.size} does not match bbox dims {(expected_w, expected_h)}; aborting partial.")
                self.render()
                return
            buf = self._epd.getbuffer(region_image)
            self._epd.display_Partial(buf, x1, y1, x2, y2)
            self._epd.sleep()
            self._render_count += 1
            print(f"[PARTIAL] Updated bbox={bbox} (count={self._render_count})")
