"""Corridor helpers over the A-Maze-ing generator's bitmask grid."""
from __future__ import annotations

import os
import random
import signal
import sys
from typing import Any, List, Optional, Set

from .constants import DIRS, ROOT, WALL, Cell

try:  # Use the assigned A-Maze-ing package as-is (installed or vendored).
    from mazegenerator.mazegenerator import MazeGenerator
except ImportError:  # pragma: no cover - fallback to the bundled copy.
    sys.path.insert(0, os.path.join(ROOT, "mazegenerator-00001-py3-none-any"))
    from mazegenerator.mazegenerator import MazeGenerator

__all__ = ["MazeGenerator", "generate_grid", "passable", "neighbour",
           "nearest_open", "reachable_from"]

# The assigned generator is used as-is, but it can take unbounded time and
# recurse deeply on larger mazes. We therefore bound each attempt with a
# wall-clock budget and retry with a fresh seed instead of freezing/crashing.
GEN_BUDGET = 2.0              # seconds allowed for a single attempt
GEN_RETRIES = 6              # attempts before giving up cleanly
_HAS_ALARM = hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer")


class _GenTimeout(Exception):
    """Raised when one generation attempt exceeds :data:`GEN_BUDGET`."""


def _on_alarm(signum: int, frame: Any) -> None:
    """SIGALRM handler: interrupt a stuck generation attempt."""
    raise _GenTimeout()


def generate_grid(w: int, h: int, seed: int) -> List[List[int]]:
    """Return a maze grid, bounding the assigned generator's runtime.

    Each attempt runs with a wall-clock budget (via ``SIGALRM`` where
    available); on timeout, deep recursion, or any other error we retry with a
    fresh seed and raise cleanly only if every attempt fails. The recursion
    limit is raised for the duration to tolerate the generator's deep DFS.
    """
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limit, 10000))
    use_alarm, prev = _HAS_ALARM, None
    if use_alarm:
        try:
            prev = signal.signal(signal.SIGALRM, _on_alarm)
        except (ValueError, OSError, RuntimeError):
            use_alarm = False        # signals unavailable / not on main thread
    attempt_seed, last = seed, "unknown error"
    try:
        for _ in range(GEN_RETRIES):
            if use_alarm:
                signal.setitimer(signal.ITIMER_REAL, GEN_BUDGET)
            try:
                grid: List[List[int]] = MazeGenerator(
                    size=(w, h), perfect=False, seed=attempt_seed).maze
                return grid
            except Exception as err:  # noqa: BLE001 - timeout/recursion/other.
                last = f"{type(err).__name__}: {err}"
                attempt_seed = random.randint(1, 2 ** 31 - 1)
            finally:
                if use_alarm:
                    signal.setitimer(signal.ITIMER_REAL, 0)
        raise RuntimeError(
            f"generator failed after {GEN_RETRIES} attempts ({last})")
    finally:
        if use_alarm and prev is not None:
            signal.signal(signal.SIGALRM, prev)
        sys.setrecursionlimit(limit)


def passable(maze: List[List[int]], x: int, y: int) -> bool:
    """A cell is walkable unless it is a solid (value 15) block."""
    return maze[y][x] != 15


def neighbour(maze: List[List[int]], w: int, h: int,
              x: int, y: int, direction: str) -> Optional[Cell]:
    """Return the open cell reached by ``direction`` or ``None`` if walled."""
    if maze[y][x] & WALL[direction]:
        return None
    dx, dy = DIRS[direction]
    nx, ny = x + dx, y + dy
    if 0 <= nx < w and 0 <= ny < h and passable(maze, nx, ny):
        return (nx, ny)
    return None


def nearest_open(maze: List[List[int]], w: int, h: int, cx: int,
                 cy: int, allowed: Optional[Set[Cell]] = None) -> Cell:
    """Find the cell closest to (cx, cy) that is walkable / in ``allowed``."""
    best, best_d = (cx, cy), 10 ** 9
    for y in range(h):
        for x in range(w):
            ok = (x, y) in allowed if allowed is not None else passable(
                maze, x, y)
            if ok and abs(x - cx) + abs(y - cy) < best_d:
                best, best_d = (x, y), abs(x - cx) + abs(y - cy)
    return best


def reachable_from(maze: List[List[int]], w: int, h: int,
                   start: Cell) -> Set[Cell]:
    """Breadth-first set of cells reachable from ``start`` through corridors."""
    seen: Set[Cell] = {start}
    queue = [start]
    while queue:
        x, y = queue.pop()
        for direction in DIRS:
            nxt = neighbour(maze, w, h, x, y, direction)
            if nxt and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen
