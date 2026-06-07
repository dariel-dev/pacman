# Project Management — Pac-Man

## Approach

Incremental, vertical-slice development driven directly by the subject's
requirement list, validated continuously with `flake8`, `mypy` and headless
(`SDL_VIDEODRIVER=dummy`) smoke tests.

## Timeline / progress

| Phase | Work | Status |
| --- | --- | --- |
| 1. Analysis | Read the subject; probe `MazeGenerator` to decode its bitmask grid (`N=1,E=2,S=4,W=8`, `15`=solid) | Done |
| 2. Core | CLI/arg validation, JSON-with-comments config with clamping, maze→corridor conversion + reachability | Done |
| 3. Gameplay | Player movement, pacgums/super-pacgums, ghost AI, lives/scoring, win/lose | Done |
| 4. Systems | Persistent top-10 highscores, level progression (≥10), per-level timer | Done |
| 5. UI | Menu, HUD, pause, game-over and victory screens, name entry | Done |
| 6. Cheats | Invincibility, freeze, fast, +life, level-skip | Done |
| 7. Polish | Smooth interpolation, bigger tiles, sized dots, fruit sprites | Done |
| 8. Packaging | Makefile, README, pyproject, .gitignore, this folder | Done |

## Analysis & technical choices

* **Modular `pacman` package**: a thin `pac-man.py` entry point drives focused
  modules (config, highscores, maze, entities, game, app) with one-way
  dependencies — satisfying the subject's "modular, reusable architecture".
* **Thin-wall grid**: each maze cell is one corridor tile with line walls,
  matching the subject's screenshot and keeping movement/AI simple.
* **Greedy ghost AI**: distance-based chase/flee with per-ghost randomness —
  enough variety, minimal code, as the subject permits.
* **JSON everywhere** (config + highscores): no extra dependencies, easy to
  inspect and robust to bad input.

## Risk analysis & mitigation

| Risk | Mitigation |
| --- | --- |
| Generator package re-installed at review | Imported as-is; vendored copy is a fallback only |
| Unreachable pacgums → level never ends | BFS reachability filters dot placement |
| Bad/updated config at defense | Clamp + log + ignore unknowns; never crash |
| Corrupt highscore file | Caught; falls back to an empty table |
| Generator raises | Caught; returns to the main menu |

## Acceptance test checklist

- [x] `python3 pac-man.py config.json` launches; wrong/empty args handled.
- [x] Missing file / invalid JSON / bad values / unknown keys → clear logs, no traceback.
- [x] Level 1 fixed seed (42); later levels random; ≥10 levels.
- [x] Pacgums, corner super-pacgums, 4 corner ghosts, centre start.
- [x] Movement (arrows/WASD), corridors only, 3 lives, respawn, game over.
- [x] Super-pacgum → frightened ghosts; eat ghost → points → respawn.
- [x] Scoring never decreases; HUD shows score/lives/level/time.
- [x] Pause/resume; game-over and victory screens with name entry.
- [x] Highscores persisted, top-10, shown in menu.
- [x] All cheats work; `flake8` and `mypy` pass clean.

## Team organisation

Two-person team: **ddervish** and **dshabani**. Decisions recorded above were
made jointly; bugs found via smoke tests were fixed immediately (e.g. dot
sizing, sprite centring, generator error handling).
https://danjel42.itch.io/pacman-42
