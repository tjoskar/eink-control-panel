"""Dialog rendering helper.

Provides `build_dialog_image(text, width=200, height=100, padding=6, shadow=True, shadow_offset=3)`
returning a PIL grayscale Image of a simple DOS-era style dialog box.

Adds an optional drop shadow along the right and bottom edges (like old
DOS / Turbo Vision dialogs) by enlarging the image canvas. Shadow uses a
slightly darker gray so it remains subtle on e‑ink.

Separated from the hardware controller so it can be reused for local
preview/testing (e.g. composing a dialog into an off-screen image and
saving to disk) without initializing the E-Ink hardware.

Usage example:
    from dialog import build_dialog_image
    img = build_dialog_image("Test meddelande", shadow=True)
    img.save("dialog_preview.png")

The wrapping is simple greedy word wrapping; left-aligned text.
Limits to ~5–6 lines to avoid overflow.
"""
from typing import List
from PIL import Image, ImageDraw
from gui_constant import text_font, colors


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_lines: int = 6) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), candidate, font=text_font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
        if len(lines) >= max_lines - 1:  # reserve space for last line
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def build_dialog_image(
    text: str,
    width: int = 200,
    height: int = 100,
    padding: int = 6,
    shadow: bool = True,
    shadow_offset: int = 3,
    shadow_color: int | None = None,
):
    """Build a dialog image with optional DOS-style shadow.

    Parameters
    ----------
    text : str
        Dialog body text.
    width : int
        Inner dialog width (excluding shadow area).
    height : int
        Inner dialog height (excluding shadow area).
    padding : int
        Inner text padding.
    shadow : bool
        Whether to draw a drop shadow (right + bottom).
    shadow_offset : int
        Pixel offset / thickness of the shadow.
    shadow_color : int | None
        Override grayscale color for shadow. Defaults to colors["light_gray"].
    """
    if shadow_color is None:
        shadow_color = colors["light_gray"]

    total_w = width + (shadow_offset if shadow else 0)
    total_h = height + (shadow_offset if shadow else 0)
    dialog_img = Image.new("L", (total_w, total_h), colors["white"])
    draw = ImageDraw.Draw(dialog_img)

    # Shadow (draw first so border sits "above")
    if shadow and shadow_offset > 0:
        # Bottom shadow strip
        draw.rectangle(
            [
                0 + shadow_offset,  # start slightly right so top-left stays clean
                height,
                shadow_offset + width - 1,
                height + shadow_offset - 1,
            ],
            fill=shadow_color,
        )
        # Right shadow strip
        draw.rectangle(
            [
                width,
                0 + shadow_offset,  # start slightly down to avoid top pixel halo
                width + shadow_offset - 1,
                height - 1,
            ],
            fill=shadow_color,
        )

    # Border
    draw.rectangle([0, 0, width - 1, height - 1], outline=colors["black"], width=1)

    max_text_width = width - padding * 2
    lines = _wrap_text(draw, text, max_text_width)
    line_height = draw.textbbox((0, 0), "Hg", font=text_font)[3]
    y_cursor = padding
    for line in lines:
        if y_cursor + line_height > height - padding:
            break
        draw.text((padding, y_cursor), line, font=text_font, fill=colors["black"])
        y_cursor += line_height + 2

    return dialog_img

__all__ = ["build_dialog_image"]
