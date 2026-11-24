# look-ahead DP + greedy row fill, error diffusion, generation
"""The heart of the program: choose which words go where.

For each row we have a target darkness per column. We pick pieces (words and
fillers) one after another so the ink of the chosen text matches the target
as closely as possible, while avoiding word overuse and words touching each
other.

Two passes per row:
  1. fill_row() first runs a *backward* dynamic programme (DP) that computes
     the best possible cost of finishing the row from every column. This is
     the "look-ahead".
  2. It then walks *forward* from the left, picking at each step the piece
     whose cost plus look-ahead is lowest.
"""
import numpy as np


def fill_row(target, groups, usage, n_words, s, rng):
    """Choose a sequence of pieces that fills one row of `target`.

    target   : 1D array, the desired darkness for each column of this row
    groups   : output of group_pieces()
    usage    : how many times each word has been used in earlier rows
    n_words  : size of the vocabulary
    s        : Settings (the penalty knobs)
    rng      : numpy random generator, for the per-row jitter

    Returns a list of piece dicts whose text, joined together, is the row.
    """
    W = len(target)                                    # row width in characters
    INF = np.float32(np.inf)                           # "impossible" cost
    total_use = usage.sum() + 1                        # +1 avoids division by zero
    share = usage / total_use * n_words                # >1 means overused across the image
    # A random cost per word, different on every row, so output doesn't look repetitive.
    jitter = rng.random(n_words).astype(np.float32) * s.jitter

    # "static" = costs that don't depend on the column: case penalty, word
    # reward, cross-row overuse, and jitter. Fillers get a flat penalty.
    static = []
    for g in groups:
        st = np.where(
            g["is_word"],
            g["case"] * g["L"] - s.word_bonus * g["L"]
            + s.repeat * share[g["wid"]] + jitter[g["wid"]],
            s.filler,
        ).astype(np.float32)
        static.append(st)

    def costs(i, gi):
        """Cost of placing each piece of group `gi` starting at column `i`.

        The "error" is the squared difference between the piece's ink and the
        target ink, summed over the piece's characters.
        """
        g = groups[gi]
        err = ((g["D"] - target[i:i + g["L"]]) ** 2).sum(1)
        c = err + static[gi]
        if target[i] < s.blank_level:                  # spaces are free in white areas
            c = np.where(g["blank"], err, c)
        return c

    # ---- Pass 1: backward DP -------------------------------------------------
    # h[i, s] = the cheapest total cost to fill columns i..W-1.
    # The second index says whether the piece just before column i was a word
    # (1) or not (0). Two words may never touch, so after a word we can only
    # place non-words.
    h = np.full((W + 1, 2), INF, np.float32)
    h[W] = 0                                           # an empty remainder costs nothing
    for i in range(W - 1, -1, -1):                     # go from the right edge to the left
        for gi, g in enumerate(groups):
            if i + g["L"] > W:                         # piece would overflow the row
                continue
            # Cost of this piece + the best cost of whatever comes after it.
            c = costs(i, gi) + h[i + g["L"], g["is_word"].astype(int)]
            h[i, 0] = min(h[i, 0], c.min())            # any piece is allowed here
            nonword = c[~g["is_word"]]                 # only non-words allowed after a word
            if nonword.size:
                h[i, 1] = min(h[i, 1], nonword.min())

    # ---- Pass 2: forward greedy walk -----------------------------------------
    seq, i, prev_word = [], 0, False
    row_count = np.zeros(n_words, np.float32)          # uses of each word in THIS row
    last = -1                                          # id of the last word placed
    while i < W:
        best, pick = INF, None
        for gi, g in enumerate(groups):
            if i + g["L"] > W:
                continue
            c = costs(i, gi) + h[i + g["L"], g["is_word"].astype(int)]
            wid = np.where(g["wid"] >= 0, g["wid"], 0)
            # Extra penalty for words already used in this row, and a much
            # bigger one if it's the same word as the one just placed.
            c = c + np.where(g["is_word"],
                             s.row_repeat * row_count[wid]
                             + np.where(g["wid"] == last, s.row_repeat * 3, 0),
                             0)
            if prev_word:                              # no two words in a row
                c = np.where(g["is_word"], INF, c)
            k = int(np.argmin(c))                      # index of the cheapest candidate
            if c[k] < best:
                best, pick = c[k], g["pcs"][k]
        seq.append(pick)
        i += len(pick["d"])                            # move past the piece we just placed
        prev_word = pick["word"] is not None
        if prev_word:
            wid = pick["wid"]
            row_count[wid] += 1
            last = wid
    return seq


def fill_image(target, groups, n_words, s, rng):
    """Fill every row of the target and return (lines, usage).

    Error diffusion: the difference between what we wanted and what we got on
    one row is spread (blurred) into the next row, so small errors don't pile up
    into visible banding.
    """
    rows = target.shape[0]
    usage = np.zeros(n_words, np.float32)              # how often each word was used overall
    lines = []
    carry = np.zeros(target.shape[1], np.float32)      # error carried down from the last row
    kernel = np.array([0.25, 0.5, 0.25], np.float32)   # blur weights for the spread
    for y in range(rows):
        row_t = np.clip(target[y] + carry, 0, 1)       # target adjusted by last row's error
        seq = fill_row(row_t, groups, usage, n_words, s, rng)
        got = np.concatenate([pc["d"] for pc in seq])  # the darkness we actually produced
        carry = s.diffuse * np.convolve(row_t - got, kernel, mode="same")
        for pc in seq:
            if pc["word"]:
                usage[pc["wid"]] += 1
        lines.append("".join(pc["text"] for pc in seq))  # glue the pieces into a string
    return lines, usage
