"""Pac-Man game package (42 activity).

A modular recreation split into focused, reusable modules:

* :mod:`pacman.constants` - shared constants and type aliases.
* :mod:`pacman.config` - JSON-with-comments configuration loading.
* :mod:`pacman.highscores` - the persistent top-10 highscore table.
* :mod:`pacman.maze` - corridor helpers over the A-Maze-ing bitmask grid.
* :mod:`pacman.entities` - the ``Ghost`` and ``Level`` entities.
* :mod:`pacman.game` - the ``Game`` state machine and main loop.
* :mod:`pacman.app` - the command-line entry point (:func:`pacman.app.main`).
"""
