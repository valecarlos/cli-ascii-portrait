# .txt / markdown code fence
"""Plain-text output: the ASCII art as a .txt file, or wrapped in a markdown code fence."""


def write_text(lines: list[str], path: str) -> None:
    """Write the rows to a plain text file, one row per line."""
    # The `with` statement opens the file and guarantees it is closed afterwards.
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_markdown(lines: list[str], path: str) -> None:
    """Write the rows inside a ``` fence so they render as a code block in markdown (e.g. GitHub)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("```text\n")
        f.write("\n".join(lines) + "\n")
        f.write("```\n")
