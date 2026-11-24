# enables `python -m cli_ascii_portrait`
"""Entry point for `python -m cli_ascii_portrait`.

Python runs this file when a package is started with -m. It hands control to
the same main() that the installed `cli-ascii-portrait` command uses.
"""
from .cli import main

if __name__ == "__main__":  # True only when run directly, not when imported
    main()
