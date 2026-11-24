# font loading + per-character ink density
"""Measure how "inky" each character looks when drawn in a font.

A character with lots of ink (like "M" or "#") is dark; a thin one (like "." or
"i") is light. The rest of the program uses these numbers to match words to
the darkness of the picture.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# __file__ is this file's path. parents[1] climbs two folders up:
# core/glyphs.py -> core/ -> cli_ascii_portrait/, where data/ lives.
DEFAULT_FONT = Path(__file__).resolve().parents[1] / "data" / "fonts" / "DejaVuSansMono-Bold.ttf"


def load_font(path: str | None = None, size: int = 14) -> ImageFont.FreeTypeFont:
    """Load a TrueType font, falling back to Pillow's built-in font if the file is missing."""
    font_path = Path(path) if path else DEFAULT_FONT
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    # Pillow ships a small default font; `size=` works on Pillow >= 10.1.
    return ImageFont.load_default(size=size)


def cell_size(font) -> tuple[int, int]:
    """Width and height in pixels of one character cell for this font.

    Width is measured from "M" (a wide letter, so it is a safe monospace estimate).
    Height is ascent + descent, i.e. the full line height.
    """
    cell_w = round(font.getlength("M"))
    ascent, descent = font.getmetrics()
    return cell_w, ascent + descent


def glyph_density(font, chars, cell_w: int, cell_h: int) -> dict[str, float]:
    """Return {character: ink coverage between 0 and 1} for every character in `chars`."""
    out = {}
    for ch in chars:
        # 'L' = 8-bit grayscale canvas, black background (0).
        im = Image.new("L", (cell_w, cell_h), 0)
        # Draw the character in white (255) on that black canvas.
        ImageDraw.Draw(im).text((0, 0), ch, fill=255, font=font)
        # Average brightness of the canvas = how much of the cell is covered by ink.
        # Divide by 255 to get a number between 0 and 1.
        out[ch] = np.asarray(im, dtype=np.float32).mean() / 255.0
    return out
