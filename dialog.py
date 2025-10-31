"""Dialog rendering helper.

Provides `build_dialog_image(text, width=200, height=100, padding=6)`
returning a PIL grayscale Image of a simple DOS-style dialog box.

This is separated from the hardware controller so it can be reused for
local preview/testing (e.g. composing a dialog into an off-screen image
and saving to disk) without initializing the E-Ink hardware.

Usage example:
    from dialog import build_dialog_image
    img = build_dialog_image("Test meddelande")
    img.save("dialog_preview.png")

The wrapping is simple greedy word wrapping; left-aligned text.
Limits to ~5-6 lines to avoid overflow.
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


def build_dialog_image(text: str, width: int = 200, height: int = 100, padding: int = 6):
    dialog_img = Image.new("L", (width, height), colors["white"])
    draw = ImageDraw.Draw(dialog_img)
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
