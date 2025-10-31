"""DisplayController encapsulates E-Ink hardware rendering logic.

Responsibilities:
- Full-screen render (compose + display).
- Debounced full render scheduling.
- Partial region update (caller supplies Image + bbox).

Note: Keep this lean; Pi Zero W has limited resources.

EPD instance is injected so callers can:
- Provide a mock for local preview/testing without SPI.
- Reuse a single hardware instance across different orchestration layers.
- Preconfigure hardware (pins, init variants) before controller usage.
"""

import threading
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from gui_constant import text_font, colors
from dialog import build_dialog_image
from config import MQTT_RENDER_DEBOUNCE_SECONDS
from compose import compose_panel
from lib.waveshare_epd.epd7in5_V2 import EPD


class DisplayController:

    def __init__(self, epd: EPD):
        """Create a controller bound to a provided EPD instance.

        Injecting the hardware driver simplifies testing (can pass a mock)
        and allows caller to manage lifecycle (e.g. reuse one EPD across
        different controllers or pre-configure pins).
        """
        # Core hardware driver (Waveshare EPD instance) provided by caller
        self._epd = epd
        # Mutex guarding any interaction with the panel (full + partial renders)
        self._render_lock = threading.Lock()
        # Event used to signal shutdown to background timers
        self._stop_event = threading.Event()
        # Debounce timer reference for scheduled full renders (MQTT bursts)
        self._render_timer = None
        # Counter of all display operations (full + partial + dialog show/restore)
        # Used to decide when to do a full clear or force full render to mitigate ghosting.
        self._render_count = 0
        # Last full panel image kept in memory so partial overlays (dialogs) can backup/restore regions.
        self._last_image = None
        # Active timer for restoring dialog region; presence means a dialog is currently visible.
        self._dialog_restore_timer = None
        # Cached region (PIL Image) beneath the dialog for later restore.
        self._dialog_backup = None
        # Bounding box (x1,y1,x2,y2) of the dialog region; pairs with _dialog_backup.
        self._dialog_bbox: Optional[Tuple[int, int, int, int]] = None
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
            # keep a copy for potential partial overlays (dialogs, etc.)
            self._last_image = img.copy()
            self._render_count += 1
            print(f"[RENDER] Full update done (count={self._render_count}, clear={do_clear})")

    # def fast_render(self):
    #     """Full panel render: init -> display -> sleep."""
    #     with self._render_lock:
    #         # Every 4th render: do a clear after init to reduce ghosting
    #         self._epd.init_fast()
    #         img = compose_panel()
    #         self._epd.display(self._epd.getbuffer(img))
    #         self._epd.sleep()
    #         # keep a copy for potential partial overlays (dialogs, etc.)
    #         self._last_image = img.copy()
    #         self._render_count += 1

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
            # keep last image in sync
            if self._last_image is not None:
                self._last_image.paste(region_image, (x1, y1))
            self._render_count += 1
            print(f"[PARTIAL] Updated bbox={bbox} (count={self._render_count})")

    # ---- Dialog / Modal ----
    def show_dialog(self, text: str, duration: float = 5.0):
        """Show a simple modal dialog (200x100) centered on the display for `duration` seconds.

        Behavior:
        - Ensures a baseline full image exists (triggers full render if missing).
        - Captures underlying region as backup.
        - Renders a white box with black border + left-aligned wrapped text.
        - After `duration` seconds the original pixels are restored via partial update.
        - If another dialog is shown before restore, previous dialog is first restored.
        """
        DIALOG_W, DIALOG_H = 200, 100
        padding = 6

        # Ensure baseline image outside the lock to avoid deadlock
        if self._last_image is None:
            print("[DIALOG] No baseline image; performing full render before showing dialog")
            self.render()

        with self._render_lock:
            # Ignore new dialog if one is already visible
            if self._dialog_restore_timer is not None:
                print("[DIALOG] Active dialog present; ignoring new request")
                return

            # Center position
            x1 = (self._epd.width - DIALOG_W) // 2
            y1 = (self._epd.height - DIALOG_H) // 2
            x2 = x1 + DIALOG_W
            y2 = y1 + DIALOG_H
            bbox = (x1, y1, x2, y2)

            # Backup underlying pixels
            self._dialog_backup = self._last_image.crop(bbox) if self._last_image else None
            self._dialog_bbox = bbox

            # Build dialog image via helper for reuse
            dialog_img = build_dialog_image(text, width=DIALOG_W, height=DIALOG_H, padding=padding)

            # Push partial (avoid ghosting mitigation override intentionally)
            self._epd.init_part()
            buf = self._epd.getbuffer(dialog_img)
            self._epd.display_Partial(buf, x1, y1, x2, y2)
            self._epd.sleep()
            self._render_count += 1
            print(f"[DIALOG] Shown at bbox={bbox} for {duration}s (count={self._render_count})")

            # Schedule restore
            def _restore():
                with self._render_lock:
                    if self._stop_event.is_set():
                        return
                    if self._dialog_backup is None or self._dialog_bbox is None:
                        return
                    rx1, ry1, rx2, ry2 = self._dialog_bbox
                    self._epd.init_part()
                    restore_buf = self._epd.getbuffer(self._dialog_backup)
                    self._epd.display_Partial(restore_buf, rx1, ry1, rx2, ry2)
                    self._epd.sleep()
                    if self._last_image is not None:
                        self._last_image.paste(self._dialog_backup, (rx1, ry1))
                    self._render_count += 1
                    print(f"[DIALOG] Restored original region bbox={self._dialog_bbox} (count={self._render_count})")
                    self._dialog_backup = None
                    self._dialog_bbox = None
                    self._dialog_restore_timer = None

            self._dialog_restore_timer = threading.Timer(duration, _restore)
            self._dialog_restore_timer.daemon = True
            self._dialog_restore_timer.start()
