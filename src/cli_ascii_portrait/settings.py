# Settings dataclass + PRESETS dict ("github", "poster", ...)
"""All the tuning knobs of the generator, in one place.

A *dataclass* is a class whose attributes are declared as fields with types and
defaults; Python writes the __init__ for us. Every field here maps 1:1 to a
command-line flag in cli.py (e.g. --word-bonus -> word_bonus).
"""
from dataclasses import dataclass, replace

# A preset is a named bundle of settings. Only the keys listed here are
# overridden when the preset is chosen.
PRESETS: dict[str, dict] = {
    "github": {"cols": 96, "aspect": 0.42, "ats": True},
}


@dataclass
class Settings:
    out: str = "out"                  # output path prefix: out.txt, out.html, ...
    cols: int = 200                   # width of the ASCII art, in characters
    aspect: float | None = None       # char width/height of the target display (None = from font)
    font: str | None = None           # path to a .ttf file (None = bundled DejaVu)
    font_size: int = 14
    words: str | None = None          # path to a custom word list (None = bundled list)
    gamma: float = 1.0                # >1 darkens midtones, <1 lightens them
    edge: float = 0.4                 # 0..1, how strongly edges are boosted
    lo: float = 25.0                  # darkness percentile mapped to "white"
    hi: float = 97.0                  # darkness percentile mapped to "full ink"
    reach: float = 1.0                # 0..1, how far up the word-density range we map to
    repeat: float = 0.3               # penalty for words overused across the whole image
    filler: float = 0.15              # penalty for each filler character
    word_bonus: float = 0.02          # reward per word character (favours words over fillers)
    jitter: float = 0.15              # random per-row cost, adds variety
    row_repeat: float = 0.4           # extra penalty when a word repeats within one row
    diffuse: float = 0.5              # how much row error carries into the next row
    seed: int = 7                     # random seed, same seed = same output
    blank_level: float = 0.08         # darkness below which spaces are free
    ats: bool = False                 # only use separators that resume parsers can split on
    invert: bool = False              # dense text = bright (for dark backgrounds)
    crop: tuple[int, int, int, int] | None = None  # (left, top, right, bottom) in source pixels
    preset: str | None = None         # name from PRESETS


def with_preset(settings: Settings) -> Settings:
    """Return a copy of `settings` with the chosen preset applied.

    `replace()` creates a new dataclass instance with some fields changed,
    so the caller's object is left untouched.
    """
    if settings.preset is None:
        return settings
    overrides = dict(PRESETS[settings.preset])
    # The user's own --aspect wins over the preset's aspect.
    if settings.aspect is not None:
        overrides.pop("aspect", None)
    return replace(settings, **overrides)
