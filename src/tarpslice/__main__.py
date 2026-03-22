"""
Package entry point — allows the application to be launched with:

    python -m tarpslice

This module simply delegates to ``cli.run()``, which starts the interactive
terminal wizard.
"""

from tarpslice.cli import run

if __name__ == "__main__":
    run()
