# e.g. ATS fillers never glue words together
"""Tests for the vocabulary and filler sets."""
from cli_ascii_portrait.core.pieces import ATS_FILLERS, build_pieces, read_words


def test_ats_fillers_never_glue_words_together():
    # These characters are kept inside tokens by text parsers (C#, CI/CD, Node.js...),
    # so they must not be used as separators in ATS mode.
    risky = set("#+./-_")
    assert not (set(ATS_FILLERS) & risky)


def test_build_pieces_adds_case_variants_once():
    dens = {c: 0.5 for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "}
    pieces = build_pieces(["api"], dens, fillers=[" "])
    texts = [pc["text"] for pc in pieces if pc["word"] == "api"]
    # lower, UPPER and Title variants, each exactly once.
    assert sorted(texts) == sorted(["api", "API", "Api"])


def test_read_words_skips_comment_lines(tmp_path):
    f = tmp_path / "words.txt"
    f.write_text("# a comment\nalpha beta\n# another\ngamma\n", encoding="utf-8")
    assert read_words(str(f)) == ["alpha", "beta", "gamma"]


def test_default_word_list_loads():
    words = read_words()
    assert len(words) > 50
    assert "Kubernetes" in words
