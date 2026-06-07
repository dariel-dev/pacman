#!/usr/bin/env bash
# build.sh — package Pac-Man as a standalone desktop build for a public
# gaming platform (itch.io / Steam), satisfying the project's "deployment"
# deliverable. It produces a self-contained executable under dist/ that needs
# no system Python and bundles the artwork, the A-Maze-ing package and a
# default config. Run it locally to verify the build, then publish with butler
# (see DEPLOYMENT.md).
set -euo pipefail
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}
APP=pacman-42

echo ">> Installing build dependencies (pyinstaller, pygame, maze generator)…"
"$PYTHON" -m pip install --upgrade pip >/dev/null
"$PYTHON" -m pip install pyinstaller pygame ./mazegenerator-00001-py3-none-any.whl

echo ">> Generating launcher (defaults to the bundled config.json)…"
cat > _pacman_launch.py <<'PY'
"""PyInstaller entry point: run Pac-Man, defaulting to the bundled config.

This wrapper lets a double-clicked build start without arguments while the
source ``pac-man.py`` still enforces the ``config.json`` argument as the
subject requires. It drives the same modular ``pacman`` package.
"""
import os
import sys

from pacman.app import main

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2:
    sys.argv.append(os.path.join(BASE, "config.json"))
main()
PY

# On Windows the --add-data separator is ';' instead of ':'.
SEP=":"
case "${OS:-}" in *Windows*) SEP=";" ;; esac

echo ">> Building with PyInstaller…"
"$PYTHON" -m PyInstaller --noconfirm --clean --windowed --name "$APP" \
    --paths . \
    --add-data "pacman-art${SEP}pacman-art" \
    --add-data "config.json${SEP}." \
    --collect-submodules pacman \
    --collect-all mazegenerator \
    _pacman_launch.py

rm -f _pacman_launch.py

echo ">> Zipping the build for itch.io upload…"
ZIP="${APP}-itch.zip"
rm -f "$ZIP"
( cd dist && zip -qr "../$ZIP" "$APP" )

echo ">> Done."
echo ">>   Executable:        ./dist/${APP}/${APP}   (test it locally first)"
echo ">>   Upload-ready file:  ${ZIP}"
echo ">>   On itch.io: New project -> Kind: Downloadable -> upload ${ZIP}"
echo ">>               (set the platform, e.g. Linux). See DEPLOYMENT.md."
