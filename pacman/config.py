"""Configuration loading: JSON-with-comments parsing, clamping and defaults."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .constants import MAX_DIM, Cell

DEFAULTS: Dict[str, Any] = {
    "highscore_filename": "highscores.json", "lives": 3, "pacgum": 42,
    "points_per_pacgum": 10, "points_per_super_pacgum": 50,
    "points_per_ghost": 200, "seed": 42, "level_max_time": 90, "level": [],
}
NUM = {"lives": (1, 99), "pacgum": (0, 9999), "points_per_pacgum": (0, 9999),
       "points_per_super_pacgum": (0, 9999), "points_per_ghost": (0, 9999),
       "seed": (1, 2 ** 31 - 1), "level_max_time": (5, 3600)}


def strip_comments(text: str) -> str:
    """Remove ``#``/``//`` line comments and ``/* */`` blocks from JSON text."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    keep = [ln for ln in text.splitlines()
            if not ln.lstrip().startswith(("#", "//"))]
    return "\n".join(keep)


def clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    """Coerce ``value`` to an int within ``[lo, hi]`` or return ``default``."""
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def parse_levels(value: Any) -> List[Cell]:
    """Read the ``level`` array into a list of clamped (width, height)."""
    out: List[Cell] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                out.append((clamp_int(item.get("width"), 7, MAX_DIM, 15),
                            clamp_int(item.get("height"), 7, MAX_DIM, 15)))
    return out


def load_config(path: str) -> Dict[str, Any]:
    """Load the JSON-with-comments config, clamping bad values to defaults."""
    cfg: Dict[str, Any] = dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as handle:
            raw = json.loads(strip_comments(handle.read()))
        if not isinstance(raw, dict):
            raise ValueError("top level must be an object")
    except FileNotFoundError:
        print(f"Config: '{path}' not found, using defaults.")
        return cfg
    except (OSError, ValueError) as err:
        print(f"Config: invalid file ({err}), using defaults.")
        return cfg
    for key, val in raw.items():
        if key == "highscore_filename":
            cfg[key] = val if isinstance(val, str) and val else cfg[key]
        elif key == "level":
            cfg[key] = parse_levels(val)
        elif key in NUM:
            lo, hi = NUM[key]
            new = clamp_int(val, lo, hi, cfg[key])
            if new != val:
                print(f"Config: '{key}'={val!r} clamped to {new}.")
            cfg[key] = new
        else:
            print(f"Config: ignoring unknown key '{key}'.")
    return cfg
