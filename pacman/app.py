"""Command-line entry point: validate the argument, load config, run the game."""
from __future__ import annotations

import sys

from .config import load_config
from .game import Game


def main() -> None:
    """Validate the CLI argument, load config and launch the game."""
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".json"):
        print("Usage: python3 pac-man.py <config.json>")
        sys.exit(1)
    try:
        Game(load_config(sys.argv[1])).run()
    except KeyboardInterrupt:
        pass
    except Exception as err:  # noqa: BLE001 - never crash with a traceback.
        print(f"Fatal error: {err}")
        sys.exit(1)
