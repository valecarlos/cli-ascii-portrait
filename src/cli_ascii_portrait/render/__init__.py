# render package: output writers (plain text, PNG, HTML)
"""Output writers. Each module turns the generated rows into one kind of file."""
from .html import write_html
from .png import render_png
from .text import write_markdown, write_text

__all__ = ["render_png", "write_html", "write_markdown", "write_text"]
