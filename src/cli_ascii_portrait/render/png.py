# mono + color PNG
"""Draw the ASCII art onto an image, in black (mono) or in the source colours."""
from PIL import Image, ImageDraw


def render_png(lines, colors, font, cell_w: int, cell_h: int, path: str, colored: bool) -> None:
    """Draw each character into its cell and save the result as a PNG.

    colored=False draws everything in black; colored=True uses the colour of
    the source picture at each cell.
    """
    width = max(len(line) for line in lines)           # longest row sets the image width
    im = Image.new("RGB", (width * cell_w, len(lines) * cell_h), "white")
    draw = ImageDraw.Draw(im)
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            if ch == " ":                              # nothing to draw for a space
                continue
            # colors[y, x] is a numpy array [r, g, b]; convert to plain ints for Pillow.
            fill = tuple(int(v) for v in colors[y, x]) if colored else (0, 0, 0)
            # Top-left corner of this character's cell is (x * cell_w, y * cell_h).
            draw.text((x * cell_w, y * cell_h), ch, fill=fill, font=font)
    im.save(path)
