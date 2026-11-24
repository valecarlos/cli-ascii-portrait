# row width exact, no word repeated in a row
"""Tests for the row filler. These use synthetic densities, so no font is needed."""
import itertools

import numpy as np

from cli_ascii_portrait.core.fill import fill_row
from cli_ascii_portrait.core.pieces import FILLERS, build_pieces, group_pieces
from cli_ascii_portrait.settings import Settings

WORDS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
         "golf", "hotel", "india", "juliet"]


def make_groups(words=WORDS):
    # Every character has the same ink (0.5), so only the penalties decide the choice.
    chars = set("".join(words)) | set("".join(w.upper() for w in words)) | set(FILLERS)
    dens = {c: 0.5 for c in chars}
    vocab = sorted({w.lower() for w in words})
    word_ids = {w: k for k, w in enumerate(vocab)}
    pieces = build_pieces(words, dens, FILLERS)
    for pc in pieces:
        pc["wid"] = word_ids.get(pc["word"], -1)
    return group_pieces(pieces, word_ids), len(vocab)


def test_row_width_is_exact():
    groups, n = make_groups()
    target = np.full(40, 0.5, np.float32)
    seq = fill_row(target, groups, np.zeros(n, np.float32), n, Settings(), np.random.default_rng(1))
    assert sum(len(pc["text"]) for pc in seq) == 40


def test_no_word_repeats_within_a_row():
    groups, n = make_groups()
    target = np.full(20, 0.5, np.float32)
    # A huge row_repeat penalty makes repeats very expensive.
    s = Settings(row_repeat=100.0)
    seq = fill_row(target, groups, np.zeros(n, np.float32), n, s, np.random.default_rng(1))
    ids = [pc["wid"] for pc in seq if pc["word"] is not None]
    assert len(ids) == len(set(ids))


def test_two_words_never_touch():
    groups, n = make_groups()
    target = np.full(30, 0.5, np.float32)
    seq = fill_row(target, groups, np.zeros(n, np.float32), n, Settings(), np.random.default_rng(3))
    for a, b in itertools.pairwise(seq):
        assert not (a["word"] is not None and b["word"] is not None)
