#!/usr/bin/env python3
"""Pac-Man: a faithful recreation built for the 42 Pacman activity.

Run with: ``python3 pac-man.py config.json``

This is a thin entry point; the game itself lives in the :mod:`pacman`
package (configuration, highscores, maze helpers, entities and the game
state machine). See ``pacman/`` for the modular implementation.
"""
from pacman.app import main

if __name__ == "__main__":
    main()
