"""Shared constants and small type aliases used across the game."""
from __future__ import annotations

import os
from typing import Dict, Tuple

Cell = Tuple[int, int]

# Project root (this package lives in <root>/pacman/) and the artwork folder.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "pacman-art")

# Movement deltas and wall bitmask (N=1 E=2 S=4 W=8) used by the maze grid.
DIRS: Dict[str, Cell] = {"up": (0, -1), "down": (0, 1),
                         "left": (-1, 0), "right": (1, 0)}
WALL: Dict[str, int] = {"up": 1, "right": 2, "down": 4, "left": 8}
OPP: Dict[str, str] = {"up": "down", "down": "up",
                       "left": "right", "right": "left"}

# Largest maze dimension we ask the assigned generator for: it slows down
# steeply and can hang beyond this, so level sizes are clamped to it.
MAX_DIM = 17

HUD_H = 40                    # height of the score/lives HUD bar in pixels
FPS = 60
P_STEP, P_FAST = 10, 6        # frames between player moves (normal / fast)
G_STEP, G_FRIGHT = 12, 18     # frames between ghost moves (normal / frightened)
