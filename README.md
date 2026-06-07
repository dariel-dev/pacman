*This activity has been created as part of the 42 curriculum by ddervish, dshabani.*

# Pac-Man

A compact, faithful recreation of the classic arcade game **Pac-Man**, written
in Python with `pygame`, with mazes produced by an external *A-Maze-ing*
generator.

**▶ Play / download on itch.io: <https://danjel42.itch.io/pacman-42>**

## Description

Guide Pac-Man through procedurally generated mazes, eat every pacgum to clear a
level, grab strawberry super-pacgums to turn the ghosts edible, snack on the
bonus apple, and chase your way through at least ten increasingly large levels —
all while four ghosts (Blinky, Pinky, Inky, Clyde) hunt you down. Beat your
friends on a persistent top-10 highscore table.

The code is organised as a small, modular `pacman` package driven by a thin
`pac-man.py` entry point.

## Instructions

Requirements: **Python 3.10+**.

```bash
make install        # installs pygame and the A-Maze-ing package
make run            # == python3 pac-man.py config.json
make debug          # run under pdb
make lint           # flake8 + mypy
make clean          # remove caches
```

Run directly:

```bash
python3 pac-man.py config.json
```

The program takes **exactly one argument**: a `.json` configuration file. Any
problem (missing file, bad value, missing key) is reported with a clear message
and **never** a Python traceback.

### Packaging / deployment

`./build.sh` builds a standalone desktop executable with PyInstaller, bundling
the artwork, the A-Maze-ing package and a default `config.json`, and zips it
ready to upload to itch.io as a downloadable build. See
[`DEPLOYMENT.md`](DEPLOYMENT.md) for the publish steps. The game is live at
<https://danjel42.itch.io/pacman-42>.

### Controls

| Action | Keys |
| --- | --- |
| Move | Arrow keys or `W` `A` `S` `D` |
| Pause / resume | `P` or `ESC` |
| Quit to menu (paused) | `Q` |
| Menu navigation | Up/Down + `Enter` |

### Cheat mode (for peer review)

Active during gameplay so a reviewer can test every feature easily:

| Key | Cheat |
| --- | --- |
| `I` | Toggle invincibility (no life lost) |
| `G` | Toggle ghost freeze |
| `F` | Toggle increased player speed |
| `L` | Add one life |
| `N` | Skip to the next level |

Enabled cheats are shown in red in the HUD.

## Configuration

The config file is JSON extended with comments: any line whose first non-space
character is `#` or `//` is ignored, and `/* ... */` blocks are stripped. Unknown
keys are ignored; out-of-range or wrong-typed values are clamped to safe
defaults and a message is logged. See `config.json` for an annotated example.

| Key | Default | Meaning |
| --- | --- | --- |
| `highscore_filename` | `highscores.json` | Where highscores are stored |
| `lives` | `3` | Starting lives (1–99) |
| `seed` | `42` | Fixed seed for level 1 |
| `level_max_time` | `90` | Seconds per level (5–3600) |
| `pacgum` | `42` | Reserved/flavour key (accepted, not gameplay-critical) |
| `points_per_pacgum` | `10` | Score for a pacgum (X) |
| `points_per_super_pacgum` | `50` | Score for a super-pacgum (Y) |
| `points_per_ghost` | `200` | Score for an edible ghost (Z) |
| `level` | *(10 sizes)* | Array of `{width, height}` maze sizes (each 7–17) |

At least **10 levels** are always played. Each dimension is clamped to the
`7`–`17` range (the maze generator slows down and can hang on larger sizes);
sizes beyond the provided list fall back to `15x15`. Level 1 uses the fixed
`seed`; later levels are random.

## Highscore

Highscores are stored as a small JSON file (`highscore_filename`). On startup the
file is loaded and sanitised; a missing or corrupt file simply yields an empty
table (no crash). Names are limited to **10 alphanumeric/space characters** and
scores to **non-negative integers**; only the **top 10** are kept. When a game
ends (win or lose) and the score qualifies, the player types a name and the
table is re-sorted and saved. The top scores are shown on the main menu and a
full top-10 view is available from it.

JSON-on-disk was chosen for its simplicity, human-readability and zero
dependencies, which makes it trivial to inspect and robust to edit.

## Maze Generation

Mazes come **entirely** from the assigned *A-Maze-ing* package
(`mazegenerator.MazeGenerator`) — it is used as-is and never modified. The loader
adapts to *its* interface:

* `MazeGenerator(size=(w, h), perfect=False, seed=s)` is constructed with
  `PERFECT=False` to obtain Pac-Man-style looping corridors.
* `.maze` returns a grid of bitmask cells (`N=1, E=2, S=4, W=8`; a set bit is a
  wall). Cells valued `15` are solid blocks — the generator's decorative "42".
* From this grid the game derives walkable corridors, places pacgums on every
  reachable cell, strawberry super-pacgums and the four ghosts in the corners,
  and Pac-Man in the centre. A breadth-first reachability pass guarantees every
  pacgum can actually be eaten.

The generator is **used as-is and never modified**, but it slows down steeply
and can hang or recurse very deeply on larger mazes. Without touching the
package, the loader stays robust on our side:

* Level dimensions are clamped to **17** (`MAX_DIM`), the generator's fast,
  reliable range.
* Each generation runs under a wall-clock budget (`SIGALRM` where available);
  on timeout, deep recursion or any error it retries with a fresh seed, and the
  recursion limit is raised for the duration.

If every attempt fails, the error is caught and the game returns cleanly to the
main menu.

## Implementation

* **Movement** is grid-based with smooth pixel interpolation between cells, so
  Pac-Man and the ghosts glide rather than teleport.
* **Ghost AI** is greedy: each ghost steps toward Pac-Man (Manhattan distance)
  when hunting and away from him while frightened, with a small per-ghost random
  bias for variety, and avoids immediate reversals.
* **Super-pacgums** start a frightened timer; eating an edible ghost banks
  points and sends it home to respawn after a delay.
* **Sprites** are the provided artwork: 12 Pac-Man frames (animated per
  direction), 4 ghosts plus the blue frightened ghost, strawberries for the
  corner super-pacgums and an apple as the roaming bonus fruit. Pacgums are
  drawn as circles.
* The game **never crashes**: argument, config, file and generator errors are
  all handled with clear messages.

## General Software Architecture

A thin `pac-man.py` entry point drives a modular `pacman` package, with each
module owning one responsibility:

* `pacman/constants.py` — shared constants and the `Cell` type alias.
* `pacman/config.py` — `load_config` / `strip_comments` / `clamp_int`: robust
  JSON-with-comments parsing with clamping and logging.
* `pacman/highscores.py` — `HighScores`: load / validate / add / persist the
  top-10 table.
* `pacman/maze.py` — corridor helpers (`neighbour`, `reachable_from`,
  `nearest_open`) over the generator's bitmask grid, plus the `MazeGenerator`
  import.
* `pacman/entities.py` — `Ghost` (home, direction, eaten/respawn timer) and
  `Level` (grid + pacgums + super-pacgums + ghosts + start).
* `pacman/game.py` — `Game`, the state machine (`menu`, `play`, `pause`,
  `scores`, `help`, `over`, `win`) owning the main loop, input, update and
  rendering.
* `pacman/app.py` — `main`: CLI argument validation and top-level error
  handling.

Dependencies flow one way (`app → game → entities → maze → constants`, with
`config` and `highscores` as leaves), so there are no import cycles and each
piece is testable in isolation.

## Project Management

The work was driven incrementally: read the subject, probe the maze
generator's interface, build a vertical slice (config → maze → render → play),
then layer scoring, ghosts, cheats, UI states and packaging, validating with
`flake8`/`mypy` and headless smoke tests throughout. Details, planning notes and
the acceptance checklist live in [`project-management/`](project-management/).

## Resources

* Pac-Man dossier / ghost behaviours — *The Pac-Man Dossier* (Jamey Pittman).
* `pygame` documentation — <https://www.pygame.org/docs/>.
* The assigned *A-Maze-ing* package source (for its bitmask grid interface).

**AI usage:** AI assistance was used to explore the maze generator's bitmask
encoding, to draft the concise single-file structure and the config/highscore
robustness handling, and to review styling for `flake8`/`mypy`. Every line was
read, understood and tested (lint, type-check and headless run-throughs) before
being kept.
