"""Persistent top-10 highscore table stored as JSON."""
from __future__ import annotations

import json
from typing import List, Tuple


class HighScores:
    """Persistent top-10 highscore table stored as JSON."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.scores: List[Tuple[str, int]] = self._load()

    def _load(self) -> List[Tuple[str, int]]:
        """Read and sanitise scores, tolerating a missing/corrupt file."""
        try:
            with open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)
            out = [(str(e.get("name", ""))[:10], int(e.get("score", 0)))
                   for e in data if int(e.get("score", 0)) >= 0]
            return sorted(out, key=lambda t: -t[1])[:10]
        except (OSError, ValueError, TypeError, AttributeError):
            return []

    def qualifies(self, score: int) -> bool:
        """Return whether ``score`` earns a spot in the top 10."""
        return score > 0 and (len(self.scores) < 10
                              or score > self.scores[-1][1])

    def add(self, name: str, score: int) -> None:
        """Add a sanitised entry (<=10 alnum/space chars) and persist."""
        clean = "".join(c for c in name if c.isalnum() or c == " ")[:10]
        entry = (clean.strip() or "Player", max(0, int(score)))
        self.scores = sorted(self.scores + [entry], key=lambda t: -t[1])[:10]
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump([{"name": n, "score": s} for n, s in self.scores],
                          handle)
        except OSError as err:
            print(f"Highscore: could not save ({err}).")
