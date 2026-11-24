# HTML output
"""Write the ASCII art as a web page, each character coloured with the source colour."""
import html as html_lib  # named differently from our own variable names to avoid confusion


def write_html(lines, colors, path: str) -> None:
    """Build an HTML page: a <pre> block with one coloured <span> per character."""
    parts = [('<!DOCTYPE html><html><head><meta charset="utf-8">'
             "<style>body{background:#fff;margin:0;display:flex;justify-content:center}"
             "pre{font:6px/6px 'DejaVu Sans Mono',Menlo,monospace;letter-spacing:0}"
             "</style></head><body><pre>")]
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            if ch == " ":
                parts.append(" ")                      # spaces need no colour
            else:
                r, g, b = colors[y, x]
                # html_lib.escape turns characters like < and & into safe HTML entities.
                parts.append(f'<span style="color:rgb({r},{g},{b})">{html_lib.escape(ch)}</span>')
        parts.append("\n")
    parts.append("</pre></body></html>")
    # join() is much faster than adding strings one by one in a loop.
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
