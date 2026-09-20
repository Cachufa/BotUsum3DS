# 1. Python project

- **Number:** 01 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Scaffold the hunt as a **Python 3** program: runnable entry point, English code, stdlib first.

## Context

Umbrella language/layout. Repo files in English. No dumps in git. One active hunt command.

**Chosen entry point:** `python3 -m botusum` (package `botusum/`). Path checks live in `botusum/paths.py`. Extra dep: `pynput` (recorded now; used from plan 03).

Required paths: Ultra Moon ROM in `resources/`, Azahar.app.

## Steps

- [x] Pick entry point (`python -m botusum`).
- [x] Extra deps only if needed (`pynput`); record them in `pyproject.toml`.
- [x] Fail loudly if ROM or Azahar.app is missing.
- [x] `.gitignore` for `logs/`, dumps under `resources/`, and venv.

## Out of scope

Emulator driving, RAM parse, Discord, hunt loop.

## Done when

`python3 -m botusum` starts (or prints a clear missing-path error) without placeholders.
