"""Game entities: a ghost and a fully-built level."""
from __future__ import annotations

from typing import Set

from .constants import Cell
from .maze import generate_grid, nearest_open, reachable_from


class Ghost:
    """A ghost with a home corner and simple chase/flee behaviour."""

    def __init__(self, home: Cell, idx: int, rand: float) -> None:
        self.home = home
        self.x, self.y = home
        self.px, self.py = home          # previous cell, for smooth drawing
        self.idx = idx
        self.rand = rand
        self.dir = "up"
        self.eaten = False
        self.timer = 0

    def reset(self) -> None:
        """Send the ghost back to its corner in an active state."""
        self.x, self.y = self.px, self.py = self.home
        self.eaten = False
        self.timer = 0


class Level:
    """Holds the maze grid and the contents placed on it."""

    def __init__(self, w: int, h: int, seed: int) -> None:
        self.grid = generate_grid(w, h, seed)
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        self.start = nearest_open(self.grid, self.w, self.h,
                                  self.w // 2, self.h // 2)
        reach = reachable_from(self.grid, self.w, self.h, self.start)
        corners = [(0, 0), (self.w - 1, 0),
                   (0, self.h - 1), (self.w - 1, self.h - 1)]
        self.supers: Set[Cell] = {nearest_open(self.grid, self.w, self.h,
                                  cx, cy, reach) for cx, cy in corners}
        self.pacgums: Set[Cell] = (reach - self.supers) - {self.start}
        self.cells = reach           # all reachable cells (fruit spawn pool)
        rng = [0.0, 1.5, 2.5, 3.5]
        self.ghosts = [Ghost(nearest_open(self.grid, self.w, self.h, cx, cy,
                       reach), i, rng[i]) for i, (cx, cy) in enumerate(corners)]
