# load, crop, edge boost, tone curve → darkness grid
"""Turn a picture into a small grid of "darkness" values, one per text character.

The output of load_target() is a 2D numpy array: rows x cols, values 0..1,
where 0 = white (no text) and 1 = black (very dense text).
"""
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def load_image(source, crop=None) -> Image.Image:
    """Open an image (path or already-open PIL image), convert to RGB, optionally crop.

    `crop` is (left, top, right, bottom) in source pixels.
    """
    im = source if isinstance(source, Image.Image) else Image.open(source)
    im = im.convert("RGB")
    if crop:
        left, top, right, bottom = crop
        if not (0 <= left < right <= im.width and 0 <= top < bottom <= im.height):
            raise ValueError(
                f"--crop {left},{top},{right},{bottom} is not a box inside the "
                f"{im.width}x{im.height} image. It is left,top,right,bottom corner "
                f"coordinates (not margins), so it needs 0 <= left < right <= {im.width} "
                f"and 0 <= top < bottom <= {im.height}. "
                f"To trim 10px from every side use --crop 10,10,{im.width - 10},{im.height - 10}"
            )
        im = im.crop(crop)
    return im


def load_target(img: Image.Image, cols: int, aspect: float, gamma: float,
                edge: float, lo: float, hi: float) -> np.ndarray:
    """Build the darkness grid that the text has to imitate.

    Steps:
      1. Grayscale, then work out how many rows the text needs. `aspect`
         corrects for characters being taller than they are wide.
      2. Optionally blend in an edge map so facial features survive the low
         resolution.
      3. Stretch the contrast and shrink to the grid size (LANCZOS = a good
         quality resize filter).
      4. Convert light -> dark (darkness = 1 - luminance), then rescale so the
         lo..hi percentiles fill the 0..1 range.
      5. Apply gamma to bend the midtones.
    """
    im = img.convert("L")  # "L" = grayscale, one brightness value per pixel
    rows = max(1, round(cols * im.height / im.width * aspect))

    if edge > 0:  # boost edges so facial features survive the low resolution
        # FIND_EDGES highlights where brightness changes quickly (outlines).
        e = np.asarray(im.filter(ImageFilter.FIND_EDGES), dtype=np.uint8).copy()
        # The filter produces junk on the image border; zero it out.
        e[:2, :] = e[-2:, :] = e[:, :2] = e[:, -2:] = 0
        edges = Image.fromarray(e).filter(ImageFilter.GaussianBlur(1))
        # Blend the original with the inverted edges (edges become dark).
        im = Image.blend(im, ImageOps.invert(edges), edge)

    im = ImageOps.autocontrast(im, cutoff=1)  # stretch brightness to use the full range
    small = im.resize((cols, rows), Image.LANCZOS)
    lum = np.asarray(small, dtype=np.float32) / 255.0   # 0..1, 1 = white
    dark = 1.0 - lum                                     # 1 = black

    # Percentile-based stretch: values below the `lo` percentile become 0,
    # values above `hi` become 1, and everything in between is rescaled.
    a, b = np.percentile(dark, lo), np.percentile(dark, hi)
    dark = np.clip((dark - a) / max(b - a, 1e-6), 0, 1)
    return dark ** gamma  # darkness: 0 = white, 1 = black


def load_colors(img: Image.Image, cols: int, rows: int) -> np.ndarray:
    """Return the picture's colours resized to the text grid: shape (rows, cols, 3), uint8."""
    im = img.convert("RGB").resize((cols, rows), Image.LANCZOS)
    return np.asarray(im)
