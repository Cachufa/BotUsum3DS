# BotUsum3DS

Shiny hunt **Pokémon Ultra Sun / Ultra Moon** in **Azahar**. Phase 1: **Poipole** (Ultra Megalopolis gift).

## Start

Homebrew Python blocks `pip3 install pynput` (PEP 668). Use the project venv from the repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install pynput
.venv/bin/python -m botusum
```

If `.venv` already exists, only the last line is needed.

Needs macOS **Accessibility** for the app that launches the command (Terminal, iTerm, Python, or Grok): System Settings → Privacy & Security → Accessibility.

Azahar: **Emulation → Configuration → Debug → Enable RPC Server**.

## What it will do

1. Interactive list → pick **Poipole**.
2. Open Azahar with `resources/Pokemon Ultra Luna.3ds`.
3. Gift cycle (timings in plan 05). Read party RAM. Shiny iff SV is **0..15**.
4. **Fail:** L+R+Start. Do not save.
5. **Shiny:** save in-game, copy `main` to `resources/main-poipole-shiny-N`, log total time, exit `0`.

**Ctrl+C** stops the bot and leaves Azahar as it is.

`python3 -m botusum` launches Azahar with the ROM (`open -a Azahar.app --args …`) and checks UDP RPC on port 45987. **Ctrl+C** stops the bot and leaves Azahar running.

`--probe-inputs` focuses Azahar, taps A / B / Start, then holds L+R+Start (soft reset) with visible delays. The hunt loop is not wired yet. See `.claude/plans/`.

## Logs

Same attempt line on stdout and `logs/attempts.txt` (append-only):

```
2026-09-20T18:00:00Z  attempt=5  duration_s=42.1  sv=1842  result=fail
```

## Requirements

- Python 3.10+ and **pynput** in a venv.
- Dump in `resources/` (gitignored):
  - `Pokemon Ultra Luna.3ds`
- Azahar: `/Applications/Azahar.app`
- Hunt save already parked in front of Dulse, Poipole not received, empty party slot, saved there.

See `CLAUDE.md` for project conventions.
