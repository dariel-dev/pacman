"""The main game state machine: menu, gameplay, pause, game-over and victory."""
from __future__ import annotations

import os
import random
from typing import Any, Dict, List, Optional, Tuple

import pygame

from .constants import (ART, DIRS, FPS, G_FRIGHT, G_STEP, HUD_H, OPP, P_FAST,
                        P_STEP, WALL, Cell)
from .entities import Ghost, Level
from .highscores import HighScores
from .maze import neighbour


class Game:
    """Main state machine: menu, gameplay, pause, game-over and victory."""

    MENU_ITEMS = ["Start Game", "View Highscores", "Instructions", "Exit"]

    def __init__(self, cfg: Dict[str, Any]) -> None:
        pygame.init()
        pygame.display.set_caption("Pac-Man")
        self.cfg = cfg
        self.scores = HighScores(cfg["highscore_filename"])
        levels = cfg["level"] or []
        self.sizes = [levels[i] if i < len(levels) else (15, 15)
                      for i in range(max(10, len(levels)))]
        self.screen = pygame.display.set_mode((640, 480))
        self.big = pygame.font.SysFont("monospace", 40, bold=True)
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.small = pygame.font.SysFont("monospace", 16)
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.running = True
        self.menu_idx = 0
        self.name = ""
        self.frame = 0
        self.invincible = self.freeze = self.fast = False

    def start_game(self) -> None:
        """Begin a fresh playthrough from level 1."""
        self.score = 0
        self.lives = self.cfg["lives"]
        self.level_idx = 0
        self.invincible = self.freeze = self.fast = False
        if self.load_level():
            self.state = "play"

    def load_level(self) -> bool:
        """Generate the current level; on generator failure return to menu."""
        w, h = self.sizes[self.level_idx]
        seed = self.cfg["seed"] if self.level_idx == 0 else random.randint(
            1, 2 ** 31 - 1)
        try:
            self.lvl = Level(w, h, seed)
        except Exception as err:  # noqa: BLE001 - maze package may raise.
            print(f"Maze generator failed ({err}); returning to menu.")
            self.state = "menu"
            return False
        self.tile = max(20, min(52, 1000 // self.lvl.w, 820 // self.lvl.h))
        self.screen = pygame.display.set_mode(
            (self.lvl.w * self.tile, HUD_H + self.lvl.h * self.tile))
        self._load_art()
        self.respawn()
        self.fruit: Optional[Tuple[Cell, pygame.Surface, int]] = None
        self.fruit_timer = 0
        self.time_left = self.cfg["level_max_time"] * FPS
        self.pcount = self.gcount = 0
        return True

    def respawn(self) -> None:
        """Reset player and ghosts to their start positions (dots untouched)."""
        self.px, self.py = self.ppx, self.ppy = self.lvl.start
        self.pdir = self.pwant = "left"
        self.fright = 0
        for ghost in self.lvl.ghosts:
            ghost.reset()

    def _load_art(self) -> None:
        """Load and scale all sprites to the current tile size."""
        def img(path: str, size: int) -> pygame.Surface:
            surf = pygame.image.load(os.path.join(ART, path)).convert_alpha()
            return pygame.transform.smoothscale(surf, (size, size))
        cs = int(self.tile * 0.66)          # characters fit inside corridors
        self.pac = {d: [img(f"pacman-{d}/{i}.png", cs) for i in (1, 2, 3)]
                    for d in DIRS}
        self.gimg = [img(f"ghosts/{n}.png", cs)
                     for n in ("blinky", "pinky", "inky", "clyde")]
        self.blue = img("ghosts/blue_ghost.png", cs)
        self.fruits = [img("other/apple.png", cs),
                       img("other/strawberry.png", cs)]

    @property
    def _pstep(self) -> int:
        """Frames between player moves (fewer = faster)."""
        return P_FAST if self.fast else P_STEP

    @property
    def _gstep(self) -> int:
        """Frames between ghost moves (slower while frightened)."""
        return G_FRIGHT if self.fright else G_STEP

    def update(self) -> None:
        """Advance one frame of gameplay (timers, movement, collisions)."""
        self.frame += 1
        if self.fright > 0:
            self.fright -= 1
        for ghost in self.lvl.ghosts:
            if ghost.eaten and ghost.timer > 0:
                ghost.timer -= 1
                if ghost.timer == 0:
                    ghost.eaten = False
        if self.fruit and self.fruit_timer > 0:
            self.fruit_timer -= 1
            if self.fruit_timer == 0:
                self.fruit = None
        elif not self.fruit and self.lvl.pacgums and random.random() < 0.0015:
            self.spawn_fruit()
        self.time_left -= 1
        if self.time_left <= 0:
            return self.end_game("over")
        self.pcount += 1
        if self.pcount >= self._pstep:
            self.pcount = 0
            self.step_player()
        self.gcount += 1
        if not self.freeze and self.gcount >= self._gstep:
            self.gcount = 0
            for ghost in self.lvl.ghosts:
                self.step_ghost(ghost)
        self.collisions()
        if not self.lvl.pacgums and not self.lvl.supers:
            self.next_level()
        return None

    def spawn_fruit(self) -> None:
        """Drop a bonus fruit (apple/strawberry) on a free reachable cell."""
        free = [c for c in self.lvl.cells
                if c not in self.lvl.pacgums and c not in self.lvl.supers
                and c != (self.px, self.py)]
        if not free:
            return
        self.fruit = (random.choice(free), self.fruits[0], 150)  # apple bonus
        self.fruit_timer = 8 * FPS

    def step_player(self) -> None:
        """Move Pac-Man one tile, honouring the buffered desired direction."""
        self.ppx, self.ppy = self.px, self.py
        for direction in dict.fromkeys([self.pwant, self.pdir]):
            nxt = neighbour(self.lvl.grid, self.lvl.w, self.lvl.h,
                            self.px, self.py, direction)
            if nxt:
                self.pdir = direction
                self.px, self.py = nxt
                break
        cell = (self.px, self.py)
        if cell in self.lvl.pacgums:
            self.lvl.pacgums.discard(cell)
            self.score += self.cfg["points_per_pacgum"]
        elif cell in self.lvl.supers:
            self.lvl.supers.discard(cell)
            self.score += self.cfg["points_per_super_pacgum"]
            self.fright = 7 * FPS
        if self.fruit and cell == self.fruit[0]:
            self.score += self.fruit[2]
            self.fruit = None

    def step_ghost(self, ghost: Ghost) -> None:
        """Move one ghost: chase the player, or flee while frightened."""
        if ghost.eaten:
            return
        ghost.px, ghost.py = ghost.x, ghost.y
        opts = [(d, n) for d in DIRS
                if d != OPP[ghost.dir]
                and (n := neighbour(self.lvl.grid, self.lvl.w, self.lvl.h,
                                    ghost.x, ghost.y, d))]
        if not opts:
            opts = [(d, n) for d in DIRS
                    if (n := neighbour(self.lvl.grid, self.lvl.w, self.lvl.h,
                                       ghost.x, ghost.y, d))]
        if not opts:
            return
        target = (self.px, self.py)

        def cost(opt: Tuple[str, Cell]) -> float:
            dist = abs(opt[1][0] - target[0]) + abs(opt[1][1] - target[1])
            return dist + ghost.rand * random.random()
        ghost.dir, (ghost.x, ghost.y) = (max(opts, key=cost) if self.fright
                                         else min(opts, key=cost))

    def collisions(self) -> None:
        """Resolve player/ghost contact: eat frightened ghosts or lose a life."""
        for ghost in self.lvl.ghosts:
            if ghost.eaten or (ghost.x, ghost.y) != (self.px, self.py):
                continue
            if self.fright > 0:
                ghost.eaten = True
                ghost.timer = 5 * FPS
                ghost.x, ghost.y = ghost.px, ghost.py = ghost.home
                self.score += self.cfg["points_per_ghost"]
            elif not self.invincible:
                self.lives -= 1
                if self.lives <= 0:
                    return self.end_game("over")
                self.respawn()
                return None
        return None

    def next_level(self) -> None:
        """Move to the next level, or trigger victory after the last one."""
        self.level_idx += 1
        if self.level_idx >= len(self.sizes):
            self.end_game("win")
        else:
            self.load_level()

    def end_game(self, state: str) -> None:
        """Enter the game-over/victory screen, prompting for a name if needed."""
        self.state = state
        self.name = ""

    def handle_events(self) -> None:
        """Dispatch input handling based on the current state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                handler = getattr(self, f"keys_{self.state}", None)
                if handler:
                    handler(event)

    def keys_menu(self, event: pygame.event.Event) -> None:
        """Navigate the main menu."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.menu_idx = (self.menu_idx - 1) % 4
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_idx = (self.menu_idx + 1) % 4
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.activate_menu()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def activate_menu(self) -> None:
        """Run the highlighted main-menu action."""
        choice = self.MENU_ITEMS[self.menu_idx]
        if choice == "Start Game":
            self.start_game()
        elif choice == "View Highscores":
            self.state = "scores"
        elif choice == "Instructions":
            self.state = "help"
        else:
            self.running = False

    def keys_play(self, event: pygame.event.Event) -> None:
        """Handle movement, pause and cheat keys during gameplay."""
        moves = {pygame.K_UP: "up", pygame.K_w: "up", pygame.K_DOWN: "down",
                 pygame.K_s: "down", pygame.K_LEFT: "left", pygame.K_a: "left",
                 pygame.K_RIGHT: "right", pygame.K_d: "right"}
        if event.key in moves:
            self.pwant = moves[event.key]
        elif event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = "pause"
        elif event.key == pygame.K_i:
            self.invincible = not self.invincible
        elif event.key == pygame.K_g:
            self.freeze = not self.freeze
        elif event.key == pygame.K_f:
            self.fast = not self.fast
        elif event.key == pygame.K_l:
            self.lives += 1
        elif event.key == pygame.K_n:
            self.next_level()

    def keys_pause(self, event: pygame.event.Event) -> None:
        """Resume the game or quit to the main menu from the pause screen."""
        if event.key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
            self.state = "play"
        elif event.key in (pygame.K_q, pygame.K_m):
            self.state = "menu"

    def keys_scores(self, event: pygame.event.Event) -> None:
        """Leave the highscore view."""
        self.state = "menu"

    keys_help = keys_scores

    def _finish(self, event: pygame.event.Event) -> None:
        """Collect the player's name on an end screen and save the score."""
        if event.key == pygame.K_RETURN:
            if self.scores.qualifies(self.score):
                self.scores.add(self.name, self.score)
            self.state = "menu"
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif len(self.name) < 10 and event.unicode.isprintable() and (
                event.unicode.isalnum() or event.unicode == " "):
            self.name += event.unicode

    keys_over = _finish
    keys_win = _finish

    def text(self, txt: str, font: pygame.font.Font, colour: Tuple[int, int,
             int], cx: int, y: int) -> None:
        """Blit ``txt`` horizontally centred on ``cx`` at vertical ``y``."""
        surf = font.render(txt, True, colour)
        self.screen.blit(surf, (cx - surf.get_width() // 2, y))

    def draw(self) -> None:
        """Render the frame for whichever state is active."""
        self.screen.fill((0, 0, 0))
        getattr(self, f"draw_{self.state}")()
        pygame.display.flip()

    def draw_menu(self) -> None:
        """Draw the title screen with menu items and the top scores."""
        cx = self.screen.get_width() // 2
        self.text("Pac-Man", self.big, (255, 255, 0), cx, 50)
        for i, item in enumerate(self.MENU_ITEMS):
            colour = (255, 255, 0) if i == self.menu_idx else (200, 200, 200)
            self.text(("> " if i == self.menu_idx else "  ") + item,
                      self.font, colour, cx, 150 + i * 36)
        self.text("highscores:", self.small, (255, 184, 81), cx, 310)
        for i, (name, sc) in enumerate(self.scores.scores[:5]):
            self.text(f"{i + 1}. {name} - {sc} pts", self.small,
                      (255, 255, 255), cx, 332 + i * 20)

    def draw_scores(self) -> None:
        """Draw the full top-10 highscore table."""
        cx = self.screen.get_width() // 2
        self.text("Highscores", self.big, (255, 255, 0), cx, 40)
        if not self.scores.scores:
            self.text("No scores yet!", self.font, (200, 200, 200), cx, 150)
        for i, (name, sc) in enumerate(self.scores.scores):
            self.text(f"{i + 1:2}. {name:<10} {sc:>6} pts", self.font,
                      (255, 255, 255), cx, 120 + i * 28)
        self.text("press any key to return", self.small, (150, 150, 150),
                  cx, self.screen.get_height() - 40)

    def draw_help(self) -> None:
        """Draw the controls and rules screen."""
        cx = self.screen.get_width() // 2
        self.text("Instructions", self.big, (255, 255, 0), cx, 40)
        lines = [
            "Move: Arrow keys or WASD",
            "Pause: P or ESC      Quit to menu: Q",
            "Eat all pacgums to clear the level.",
            "Super-pacgums (strawberries, corners) scare ghosts.",
            "Eat edible (blue) ghosts for bonus points.",
            "Grab the bonus apple for extra points.",
            "Avoid ghosts or you lose a life (3 to start).",
            "",
            "Cheats (in-game):",
            "I invincible   G freeze ghosts   F fast",
            "L +1 life      N skip level",
        ]
        for i, line in enumerate(lines):
            self.text(line, self.small, (220, 220, 220), cx, 120 + i * 24)
        self.text("press any key to return", self.small, (150, 150, 150),
                  cx, self.screen.get_height() - 40)

    def draw_play(self) -> None:
        """Draw the maze, dots, entities and the HUD."""
        grid, t = self.lvl.grid, self.tile
        self._draw_walls(grid, t)
        gum, sr = (255, 203, 158), max(3, t // 8)
        for (x, y) in self.lvl.pacgums:
            pygame.draw.circle(self.screen, gum,
                               (x * t + t // 2, HUD_H + y * t + t // 2), sr)
        for (x, y) in self.lvl.supers:           # strawberries mark the corners
            self._blit_at(self.fruits[1], x, y)
        if self.fruit:
            self._blit_at(self.fruit[1], self.fruit[0][0], self.fruit[0][1])
        gfrac = min(1.0, self.gcount / self._gstep)
        for ghost in self.lvl.ghosts:
            if ghost.eaten:                      # regenerating in its zone
                faded = self.gimg[ghost.idx].copy()
                faded.set_alpha(90)
                self._blit_at(faded, ghost.x, ghost.y)
                continue
            sprite = self.blue if (self.fright > 0 and
                                   (self.fright > 120 or self.frame % 12 < 6)
                                   ) else self.gimg[ghost.idx]
            self._blit_at(sprite, ghost.px + (ghost.x - ghost.px) * gfrac,
                          ghost.py + (ghost.y - ghost.py) * gfrac)
        pfrac = min(1.0, self.pcount / self._pstep)
        self._blit_at(self.pac[self.pdir][(self.frame // 4) % 3],
                      self.ppx + (self.px - self.ppx) * pfrac,
                      self.ppy + (self.py - self.ppy) * pfrac)
        self._draw_hud()

    def _draw_walls(self, grid: List[List[int]], t: int) -> None:
        """Render hollow, rounded blue 'tube' walls (carved interiors)."""
        blue, bg = (33, 33, 222), (0, 0, 0)
        wt = max(4, int(t * 0.34))
        h = wt // 2
        lw = max(2, t // 11)
        bars, solids = [], []
        for y in range(self.lvl.h):
            for x in range(self.lvl.w):
                x0, y0 = x * t, HUD_H + y * t
                if grid[y][x] == 15:
                    solids.append((x0, y0))
                    continue
                v = grid[y][x]
                if v & WALL["up"]:
                    bars.append((x0 - h, y0 - h, t + wt, wt))
                if v & WALL["down"]:
                    bars.append((x0 - h, y0 + t - h, t + wt, wt))
                if v & WALL["left"]:
                    bars.append((x0 - h, y0 - h, wt, t + wt))
                if v & WALL["right"]:
                    bars.append((x0 + t - h, y0 - h, wt, t + wt))
        for bx, by, bw, bh in bars:
            pygame.draw.rect(self.screen, blue, (bx, by, bw, bh),
                             border_radius=h)
        for bx, by, bw, bh in bars:              # carve interiors -> outlines
            if bw - 2 * lw > 0 and bh - 2 * lw > 0:
                pygame.draw.rect(self.screen, bg, (bx + lw, by + lw,
                                 bw - 2 * lw, bh - 2 * lw),
                                 border_radius=max(0, h - lw))
        for x0, y0 in solids:                    # the generator's solid "42"
            pygame.draw.rect(self.screen, blue, (x0, y0, t, t))

    def _blit_at(self, sprite: pygame.Surface, gx: float, gy: float) -> None:
        """Blit a sprite centred on the cell at a fractional grid position."""
        off = (self.tile - sprite.get_width()) // 2
        self.screen.blit(sprite, (round(gx * self.tile) + off,
                                  HUD_H + round(gy * self.tile) + off))

    def _draw_hud(self) -> None:
        """Draw the always-visible score/lives/level/time bar."""
        cheats = "".join(c for c, on in (("I", self.invincible),
                         ("G", self.freeze), ("F", self.fast)) if on)
        hud = (f"Score:{self.score}  Lives:{self.lives}  "
               f"Level:{self.level_idx + 1}  Time:{self.time_left // FPS}")
        self.screen.blit(self.small.render(hud, True, (255, 255, 255)), (6, 12))
        if cheats:
            surf = self.small.render("CHEAT:" + cheats, True, (255, 80, 80))
            self.screen.blit(surf, (self.screen.get_width() -
                                    surf.get_width() - 6, 12))

    def draw_pause(self) -> None:
        """Overlay the pause menu on the frozen board."""
        self.draw_play()
        w, h = self.screen.get_size()
        veil = pygame.Surface((w, h))
        veil.set_alpha(180)
        self.screen.blit(veil, (0, 0))
        self.text("Paused", self.big, (255, 255, 0), w // 2, h // 2 - 60)
        self.text("P / ESC - Resume", self.font, (255, 255, 255),
                  w // 2, h // 2)
        self.text("Q - Quit to main menu", self.font, (255, 255, 255),
                  w // 2, h // 2 + 36)

    def _draw_end(self, title: str, colour: Tuple[int, int, int]) -> None:
        """Shared game-over / victory screen with name entry."""
        cx, cy = self.screen.get_width() // 2, 60
        self.text(title, self.big, colour, cx, cy)
        self.text(f"Final score: {self.score}", self.font, (255, 255, 255),
                  cx, cy + 70)
        if self.scores.qualifies(self.score):
            self.text("Enter your name:", self.font, (200, 200, 200),
                      cx, cy + 130)
            self.text(self.name + "_", self.big, (255, 255, 0), cx, cy + 165)
            self.text("press ENTER to save", self.small, (150, 150, 150),
                      cx, cy + 230)
        else:
            self.text("press ENTER to continue", self.small, (150, 150, 150),
                      cx, cy + 150)

    def draw_over(self) -> None:
        """Game-over screen."""
        self._draw_end("Game Over", (255, 60, 60))

    def draw_win(self) -> None:
        """Victory screen."""
        self._draw_end("You Win! Waka-waka!", (80, 255, 80))

    def run(self) -> None:
        """Run the main loop until the player quits."""
        while self.running:
            self.handle_events()
            if self.state == "play":
                self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
