# (added) generate(): runs the whole pipeline from image to text rows
"""Glue code: runs every step in order and returns the result.

This lives in its own file so that the package __init__.py and cli.py can both
import it without importing each other (a circular import).
"""
from dataclasses import dataclass

import numpy as np

from .core.fill import fill_image
from .core.glyphs import cell_size, glyph_density, load_font
from .core.image import load_colors, load_image, load_target
from .core.pieces import ATS_FILLERS, FILLERS, build_pieces, group_pieces, read_words
from .settings import Settings, with_preset


@dataclass
class Result:
    """Everything the renderers need to write the output files."""
    lines: list[str]        # the ASCII art, one string per row
    colors: np.ndarray      # (rows, cols, 3) colour of the source at each cell
    font: object            # font used, needed to draw the PNGs
    cell_w: int             # pixel width of one character cell
    cell_h: int             # pixel height of one character cell
    vocab: list[str]        # all words that were available
    usage: np.ndarray       # how many times each vocab word was used


def generate(image, settings: Settings | None = None) -> Result:
    """Turn an image (path or PIL image) into word-based ASCII art.

    `settings` is optional; without it the defaults are used.
    """
    s = with_preset(settings or Settings())
    img = load_image(image, s.crop)
    rng = np.random.default_rng(s.seed)               # seeded, so runs are repeatable

    # --- font and character sizes -------------------------------------------
    words = read_words(s.words)
    font = load_font(s.font, s.font_size)
    cell_w, cell_h = cell_size(font)
    # Target aspect: characters are usually taller than wide, so the image
    # gets fewer rows than a naive resize would give.
    aspect = s.aspect or cell_w / cell_h

    # --- ink density of every character we might need -----------------------
    fillers = ATS_FILLERS if s.ats else FILLERS
    # Set union (|) of all the characters used: letters in any case, plus fillers.
    charset = set("".join(words)) | set("".join(w.upper() + w.lower() for w in words)) | set(fillers)
    dens = glyph_density(font, charset, cell_w, cell_h)
    dmax = max(dens.values())
    dens = {c: v / dmax for c, v in dens.items()}     # scale so the densest char is 1.0

    pieces = build_pieces(words, dens, fillers)

    # Map the image darkness onto the density range that words can actually
    # reach, so dark areas become UPPERCASE words rather than walls of '#'.
    # `reach` is the density at the `s.reach` percentile of all word pieces.
    word_dens = sorted(float(pc["d"].mean()) for pc in pieces if pc["word"])
    reach = word_dens[min(len(word_dens) - 1, int(len(word_dens) * s.reach))]

    # --- the picture as a darkness grid -------------------------------------
    target = load_target(img, s.cols, aspect, s.gamma, s.edge, s.lo, s.hi)
    if s.invert:                                      # light text on dark backgrounds
        target = 1.0 - target
    target = target * reach

    # --- connect pieces to vocabulary ids and fill ---------------------------
    vocab = sorted({pc["word"] for pc in pieces if pc["word"]})
    word_ids = {w: k for k, w in enumerate(vocab)}    # word -> integer id
    for pc in pieces:
        pc["wid"] = word_ids.get(pc["word"], -1)      # -1 for fillers
    groups = group_pieces(pieces, word_ids)
    lines, usage = fill_image(target, groups, len(vocab), s, rng)

    colors = load_colors(img, s.cols, len(lines))
    return Result(lines, colors, font, cell_w, cell_h, vocab, usage)
