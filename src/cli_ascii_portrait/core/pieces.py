# word variants, filler sets (default / ATS), grouping
"""The vocabulary the generator is allowed to write with.

A "piece" is one thing that can be placed on a row: a word (in some case),
or a single filler character. Each piece knows its text and the ink density
of each of its characters, which is what the fill algorithm compares against
the picture.
"""
from collections import defaultdict
from pathlib import Path

import numpy as np

# Same idea as DEFAULT_FONT: parents[1] is the cli_ascii_portrait/ folder.
DEFAULT_WORDS_FILE = Path(__file__).resolve().parents[1] / "data" / "words.txt"

# Stand-alone characters to plug gaps between words.
FILLERS = list(" .,-:;=+/_#")
# Characters every text extractor treats as a word boundary. '#', '+', '.',
# '/', '-', '_' are avoided: tokenizers keep them inside tokens (C#, C++,
# Node.js, CI/CD, snake_case), which would glue neighbouring words together.
ATS_FILLERS = list(" ,;:|=")


def read_words(path: str | None = None) -> list[str]:
    """Read the word list. Lines starting with '#' are comments; everything else is split on whitespace."""
    file = Path(path) if path else DEFAULT_WORDS_FILE
    text = file.read_text(encoding="utf-8")
    # A list comprehension: keep only the lines that are not comments.
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    return " ".join(lines).split()


def build_pieces(words, dens, fillers):
    """Create every placeable piece, each with its per-character density vector.

    Each word is added in up to four casings. `case_pen` is a small penalty
    that makes the algorithm prefer the natural casing: as written, then
    lower, then Title, and UPPER last. Fillers are single characters.
    """
    pieces = []
    for w in words:
        # dict: text -> case penalty. `setdefault` only adds a key if it's new,
        # so e.g. a word that is already lowercase isn't added twice.
        variants = {w: 0.0}
        variants.setdefault(w.lower(), 0.004)
        variants.setdefault(w.upper(), 0.010)
        variants.setdefault(w[:1].upper() + w[1:], 0.002)
        for text, case_pen in variants.items():
            pieces.append({
                "text": text,                 # what gets printed
                "word": w.lower(),            # the base word, used for repeat penalties
                "case_pen": case_pen,
                # One density number per character, as a numpy array.
                "d": np.array([dens[c] for c in text], np.float32),
            })
    for f in fillers:
        pieces.append({"text": f, "word": None, "case_pen": 0.0,
                           "d": np.array([dens[f]], np.float32)})
    return pieces


def group_pieces(pieces, word_ids):
    """Bundle pieces of the same length together.

    All pieces in one group share a length L, so their densities can be stacked
    into one 2D array D. Then the cost of every candidate is computed with a
    single numpy operation instead of a Python loop. This is the main speed trick.
    """
    groups = defaultdict(list)          # length -> list of pieces
    for pc in pieces:
        groups[len(pc["d"])].append(pc)
    out = []
    for L, pcs in sorted(groups.items()):   # sorted() gives lengths in order
        out.append({
            "L": L,
            "pcs": pcs,                                        # the original piece dicts
            "D": np.stack([pc["d"] for pc in pcs]),            # shape (n_pieces, L)
            "is_word": np.array([pc["word"] is not None for pc in pcs]),
            "wid": np.array([word_ids.get(pc["word"], -1) for pc in pcs]),  # -1 for fillers
            "case": np.array([pc["case_pen"] for pc in pcs], np.float32),
            "blank": np.array([pc["text"] == " " for pc in pcs]),
        })
    return out
