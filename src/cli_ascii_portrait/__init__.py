# public API: generate(), Settings
"""cli_ascii_portrait: turn an image into ASCII art built from words.

Use it from Python:

    from cli_ascii_portrait import Settings, generate
    result = generate("photo.png", Settings(cols=120))
    print("\\n".join(result.lines))

`main` is re-exported because pyproject.toml points the command at it.
"""
from .cli import main
from .pipeline import Result, generate
from .settings import Settings

__all__ = ["Result", "Settings", "generate", "main"]
