# BotUsum3DS

Shiny hunt **Pokémon Ultra Sun / Ultra Moon** in **Azahar**. Hunts: **Poipole** (Ultra Megalopolis gift) and **Type: Null** (Ancient Poni Path gift).

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

1. Interactive list → pick **Poipole** or **Type: Null**.
2. Open Azahar with `resources/Pokemon Ultra Luna.3ds`.
3. Gift cycle. Read party RAM. Shiny iff SV is **0..15**.
4. **Fail:** L+R+Start. Do not save.
5. **Shiny:** save in-game, copy `main`, log total time, exit `0`.

**Ctrl+C** stops the bot and leaves Azahar as it is.

`python3 -m botusum` shows the hunt list, then launches Azahar with the ROM (`open -a Azahar.app --args …`) and checks UDP RPC on port 45987. **Ctrl+C** stops the bot and leaves Azahar running.

`--hunt poipole` or `--hunt type-null` skips the list. An unimplemented row prints `not implemented` and does not start Azahar. `--probe-inputs` skips the list, focuses Azahar, taps A / B / Start, then holds L+R+Start (soft reset). `--parse-sv` skips the list, reads party RAM over RPC, decrypts PK7, and prints species / PID / TID / SID / `sv` / shiny (does not hunt, does not read the on-disk `main`). Default hunt repeats the Poipole cycle until SV &lt; 16: mash A for 31 seconds, tap B (no nickname), mash A for 1 second, read party RAM, log the attempt. **Fail:** L+R+Start, no in-game save. **Miss** (`sv=-1`): extra L+R+Start (not an Azahar relaunch). **Shiny:** wait 2s, X, Y, then A, A to save, copy `resources/main-poipole-shiny-N`, log `logs/shiny.txt`, exit `0`. `--max-attempts N` stops after N logged attempts. `--force-shiny` alone copies without hunting. `--hunt poipole --force-shiny` does one receive then that in-game save (timing test). A later launch whose last `logs/attempts.txt` line is `result=shiny` does not start Poipole again. **Ctrl+C** stops the bot and leaves Azahar. See `.claude/plans/`.

**Type: Null** (`--hunt type-null`, species 772, 1/4096). Save one step left of the Ancient Poni Path trigger (one circle-pad step right starts Wicke and Hau). Leave a free party slot and at least one free box, or Wicke defers the gift to Aether Paradise. The first attempt waits 6 seconds with no input while the ROM loads. Every attempt then mashes A for 5 seconds (title and continue), holds circle-pad right for 0.2 seconds (the Right arrow, not D-pad H), waits 0.5 seconds, mashes A for 40 seconds, taps B (no nickname), and mashes A for 1 second. Soft reset returns to the title, so later attempts skip the 6 second wait. **Fail** and **miss** soft-reset and do not save. **Shiny:** mash A for 20 seconds through the post-receive scene, then one focused burst: X, wait 0.5 seconds, Y, wait 0.5 seconds, A, wait 0.5 seconds, A. Copy `resources/main-type-null-shiny-N`. Logs go to `logs/type-null/`, not `logs/attempts.txt`. `--hunt type-null --force-shiny` does one receive and that save even when SV is not shiny. That save consumes the gift; put the parked hunt `main` back before hunting again.

## Logs

Poipole uses `logs/`. Type: Null uses `logs/type-null/`. Same attempt line on stdout and `attempts.txt` (append-only; never truncated). Restarting continues `attempt` from the last line in that directory. Hunt start is kept in `hunt_started.txt`. A shiny also appends `shiny.txt`:

```
2026-09-20T18:00:00Z  attempt=5  duration_s=42.1  sv=1842  result=fail
SHINY  2026-09-20T19:10:00Z  attempts=3759  total_s=123456.7  sv=7  save=resources/main-poipole-shiny-1
```

## Requirements

- Python 3.10+ and **pynput** in a venv.
- Dump in `resources/` (gitignored):
  - `Pokemon Ultra Luna.3ds`
- Azahar: `/Applications/Azahar.app`
- Poipole hunt save parked in front of Dulse, Poipole not received, empty party slot.
- Type: Null hunt save parked one step left of the Ancient Poni Path gift trigger, gift not received, one free party slot and one free box.

See `CLAUDE.md` for project conventions.
