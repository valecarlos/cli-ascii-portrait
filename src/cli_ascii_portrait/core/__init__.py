# core package: image processing, glyph metrics, word pieces and row filling
"""The algorithm, split by job:

- image.py   : picture -> darkness grid
- glyphs.py  : font -> ink density of each character
- pieces.py  : word list -> placeable pieces, grouped by length
- fill.py    : darkness grid + pieces -> rows of text
"""
