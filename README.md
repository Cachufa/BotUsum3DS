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

`python3 -m botusum` shows the hunt list, then launches Azahar with the ROM (`open -a Azahar.app --args …`) and checks UDP RPC on port 45987. **Ctrl+C** stops the bot and leaves Azahar running.

`--hunt poipole` skips the list. An unimplemented row prints `not implemented` and does not start Azahar. `--probe-inputs` skips the list, focuses Azahar, taps A / B / Start, then holds L+R+Start (soft reset). `--parse-sv` skips the list, reads party RAM over RPC, decrypts PK7, and prints species / PID / TID / SID / `sv` / shiny (does not hunt, does not read the on-disk `main`). Default hunt repeats the Poipole cycle until SV &lt; 16: mash A for 31 seconds, tap B (no nickname), mash A for 1 second, read party RAM, log the attempt. **Fail:** L+R+Start, no in-game save. **Miss** (`sv=-1`): extra L+R+Start (not an Azahar relaunch). **Shiny:** wait 2s, X, Y, then A, A to save, copy `resources/main-poipole-shiny-N`, log `logs/shiny.txt`, exit `0`. `--max-attempts N` stops after N logged attempts. `--force-shiny` alone copies without hunting. `--hunt poipole --force-shiny` does one receive then that in-game save (timing test). A later launch whose last log line is `result=shiny` does not hunt. **Ctrl+C** stops the bot and leaves Azahar. See `.claude/plans/`.

## Logs

Same attempt line on stdout and `logs/attempts.txt` (append-only; never truncated). Restarting continues `attempt` from the last line. Hunt start is kept in `logs/hunt_started.txt`. A shiny also appends `logs/shiny.txt`:

```
2026-09-20T18:00:00Z  attempt=5  duration_s=42.1  sv=1842  result=fail
SHINY  2026-09-20T19:10:00Z  attempts=3759  total_s=123456.7  sv=7  save=resources/main-poipole-shiny-1
```

## Requirements

- Python 3.10+ and **pynput** in a venv.
- Dump in `resources/` (gitignored):
  - `Pokemon Ultra Luna.3ds`
- Azahar: `/Applications/Azahar.app`
- Hunt save already parked in front of Dulse, Poipole not received, empty party slot, saved there.

See `CLAUDE.md` for project conventions.
