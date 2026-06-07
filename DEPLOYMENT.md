# Deployment (itch.io)

The subject requires the game to be deployable to a public gaming platform as a
**free, unlisted/private** build (mandatory part + Chapter 7). These are the
steps; the final publish is done from your own itch.io account.

## 1. Build a standalone executable

```bash
./build.sh
```

This bundles the artwork, the A-Maze-ing package and a default `config.json`
into a self-contained build under `dist/pacman-42/`. Verify it runs:

```bash
./dist/pacman-42/pacman-42
```

> Build on the OS you want to ship: PyInstaller does not cross-compile, so a
> Linux run produces a Linux build, Windows a Windows build, etc. On Windows the
> `--add-data` separator is `;` (handled automatically by `build.sh`).

## 2. Publish with butler

[butler](https://itch.io/docs/butler/) is itch.io's command-line uploader.

```bash
# One-time: install butler and log in
butler login

# Create a project page on itch.io (Dashboard → Create new project),
# set visibility to "Restricted / unlisted" and price to "No payment / free".

# Push the build (adjust the channel/OS as needed):
butler push dist/pacman-42 danjel42/pacman-42:linux
```

Re-running `butler push` uploads new versions; itch.io handles patching.

## 3. Record the link

The game is published here so reviewers can install and launch it from the
platform:

- **itch.io page: <https://danjel42.itch.io/pacman-42>**
