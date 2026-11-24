# argument parsing, presets → Settings, calls core, writes output
"""Command-line interface: reads flags, builds Settings, runs generate(), saves files."""
import argparse
import dataclasses

from .pipeline import generate
from .render import render_png, write_html, write_text
from .settings import PRESETS, Settings, with_preset


def parse_crop(text: str) -> tuple[int, int, int, int]:
    """Turn "left,top,right,bottom" into a tuple of four ints."""
    parts = [int(v) for v in text.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--crop needs four numbers: left,top,right,bottom")
    return tuple(parts)  # type: ignore[return-value]


def build_parser() -> argparse.ArgumentParser:
    """Describe every command-line flag. argparse does the parsing and the --help text."""
    ap = argparse.ArgumentParser(prog="cli-ascii-portrait",
                                 description="Turn an image into ASCII art made of words.")
    ap.add_argument("image", help="path to the input image")
    ap.add_argument("-o", "--out", default="out", help="output path prefix")
    ap.add_argument("--cols", type=int, default=200, help="width in characters")
    ap.add_argument("--words", help="file with words (whitespace separated, # lines are comments)")
    ap.add_argument("--font", help="path to a .ttf font (default: bundled DejaVu Sans Mono Bold)")
    ap.add_argument("--font-size", type=int, default=14)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--edge", type=float, default=0.4, help="edge boost strength")
    ap.add_argument("--repeat", type=float, default=0.3, help="penalty for overused words")
    ap.add_argument("--filler", type=float, default=0.15, help="penalty per filler char")
    ap.add_argument("--word-bonus", type=float, default=0.02, help="reward per word char")
    ap.add_argument("--jitter", type=float, default=0.15, help="random per-row word cost (variety)")
    ap.add_argument("--lo", type=float, default=25, help="darkness percentile mapped to white")
    ap.add_argument("--hi", type=float, default=97, help="darkness percentile mapped to full ink")
    ap.add_argument("--reach", type=float, default=1.0)
    ap.add_argument("--diffuse", type=float, default=0.5, help="row-to-row error diffusion")
    ap.add_argument("--row-repeat", type=float, default=0.4,
                    help="extra cost each time a word reappears in the same row")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--blank-level", type=float, default=0.08,
                    help="darkness below which spaces are free")
    ap.add_argument("--aspect", type=float, help="char width/height of the target display")
    ap.add_argument("--ats", action="store_true",
                    help="only use separators that split words for parsers")
    ap.add_argument("--invert", action="store_true", help="dense text = bright (dark backgrounds)")
    ap.add_argument("--crop", type=parse_crop, help="crop box corners left,top,right,bottom in source pixels (not margins)")
    ap.add_argument("--preset", choices=sorted(PRESETS),
                    help="github: 96 cols, GitHub code-block aspect, --ats")
    return ap


def main(argv: list[str] | None = None) -> None:
    """Entry point. `argv=None` means "read sys.argv", which is what the real command does.

    Tests can pass their own list instead, e.g. main(["photo.png", "--cols", "40"]).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Copy every argument whose name matches a Settings field into Settings.
    # `args` is a Namespace (attribute-style object); vars() turns it into a dict.
    # `image` is not a setting, so it is skipped.
    field_names = {f.name for f in dataclasses.fields(Settings)}
    settings = Settings(**{k: v for k, v in vars(args).items() if k in field_names})

    # Apply the preset here (not only inside generate) so that the summary
    # below reports the real width, e.g. 96 columns for --preset github.
    settings = with_preset(settings)
    try:
        result = generate(args.image, settings)
    except ValueError as e:                            # e.g. a bad --crop box
        parser.error(str(e))                           # prints usage + message, exits with code 2

    out = settings.out
    rows = len(result.lines)
    write_text(result.lines, f"{out}.txt")
    render_png(result.lines, result.colors, result.font, result.cell_w, result.cell_h,
               f"{out}_mono.png", colored=False)
    render_png(result.lines, result.colors, result.font, result.cell_w, result.cell_h,
               f"{out}_color.png", colored=True)
    write_html(result.lines, result.colors, f"{out}.html")

    # Summary: the most used words, sorted by count (highest first).
    used = sorted(((result.vocab[k], int(c)) for k, c in enumerate(result.usage) if c),
                  key=lambda kv: -kv[1])
    print(f"{settings.cols}x{rows} chars, {len(used)}/{len(result.vocab)} words used")
    print("top:", used[:10])
