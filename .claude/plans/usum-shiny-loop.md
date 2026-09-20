# USUM shiny loop (requirements)

This file is the **umbrella** snapshot. Do not delete it.

- **Number:** 00 (umbrella)
- **Status:** requirements — not started

Work is split into:

| # | Plan | Topic | Status |
|---|------|--------|--------|
| 01 | [python-project.md](python-project.md) | Python layout, CLI, deps, gitignore | done |
| 02 | [azahar-process.md](azahar-process.md) | Launch Azahar, load ROM, RPC server | done |
| 03 | [inputs-macos.md](inputs-macos.md) | Keyboard, window focus, soft reset | done |
| 04 | [picker.md](picker.md) | Interactive hunt list (Poipole first) | done |
| 05 | [poipole-sequence.md](poipole-sequence.md) | Calibrate gift dialogue / receive / save | done |
| 06 | [parse-shiny-value.md](parse-shiny-value.md) | RAM party, PK7 decrypt, SV | done |
| 07 | [logging.md](logging.md) | Terminal + files, resume attempt number | done |
| 08 | [when-shiny.md](when-shiny.md) | In-game save, incremental copy, stop | not started |
| 09 | [hunt-loop.md](hunt-loop.md) | Wire the pieces into the repeat loop | in progress |

## Goal

A **Python** program on macOS that shiny-hunts Pokémon in **Ultra Sun / Ultra Moon** via **Azahar**. Phase 1 is **Poipole only**. The CLI shows an interactive list of hunts; picking Poipole launches Azahar, loads the `.3ds` from `resources/`, runs the gift cycle, reads RAM to test shiny, soft-resets on fail, and on hit saves in-game and copies the save into `resources/` with an incremental `-shiny-N` suffix.

Each attempt is logged to a text file **and** to the terminal (attempt number, duration, shiny value). A shiny also logs total hunt time.

## Context (this machine)

Repo: `/Users/cachufa/Documents/Git/BotUsum3DS`.

Mirror **BotJirachiGC** conventions: English code/comments/plans, Spanish chat, no git commit/push unless the user says so, `resources/` dumps are not code.

| Item | Value |
|------|--------|
| Azahar | `/Applications/Azahar.app` |
| Current ROM | `resources/Pokemon Ultra Luna.3ds` (from `~/Downloads/Pokemon Ultra Luna.3ds`) |
| Ultra Moon title ID | `00040000001B5100` |
| In-game save | `~/Library/Application Support/Azahar/sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/title/00040000/001b5100/data/00000001/main` (~435 KB) |
| RPC | UDP `127.0.0.1:45987` (`citra.py`). Currently `enable_rpc_server=false` — must be turned on |
| Default 3DS keys | A=`A` B=`S` X=`Z` Y=`X` L=`Q` R=`W` Start=`M` Select=`N` D-pad T/G/F/H |
| Soft reset | L+R+Start → hold `Q`+`W`+`M` |
| Python | Homebrew 3.14.7; venv + `pynput` (PEP 668 blocks system pip) |
| Template | `Documents/Git/BotJirachiGC` |

Ultra Sun is wired later (typical title ID `00040000001B5000`). Only an Ultra Moon dump exists now.

Poipole is the Ultra Megalopolis gift (Dulse in Moon / Soliera in Sun). **Not shiny-locked.** Odds **1/4096**. Shiny Charm does **not** apply. Synchronize **does** apply for nature.

## Assumptions (edit this file if wrong)

1. The hunt save is already (or will be) parked **in front of the NPC**, Poipole **not** received, **empty party slot**, **saved there**. Soft reset reloads that save. Never save on a fail.
2. ROM lives at `resources/Pokemon Ultra Luna.3ds` (copy or symlink; gitignored).
3. Shiny copies are named `main-poipole-shiny-N` so later hunts do not collide.
4. Picker is a **terminal** list, not a GUI.
5. Package name `botusum`. Entry: `python3 -m botusum`.
6. Plan 05 timings are **measured**, not guessed.

## Language and layout

- Implementation language: **Python 3** (stdlib first). Extra deps: `pynput`. Vendor Azahar’s `citra.py` for RPC.
- Entry point: `python3 -m botusum`.
- Code, comments, identifiers, plan files: English.
- Chat with the user may be Spanish.

Proposed tree:

```
BotUsum3DS/
  CLAUDE.md
  README.md
  pyproject.toml
  .gitignore
  .claude/plans/
  .claude/rules/
  botusum/
    __main__.py
    paths.py
    azahar.py
    rpc.py
    inputs.py
    party.py
    sequence.py
    huntlog.py
    shiny.py
    picker.py
  resources/
  logs/
```

## Picker

Terminal list. Phase 1:

```
[1] Poipole  (Ultra Megalopolis gift, 1/4096)
```

Arrow keys or number + Enter. Each future hunt is a registry row (`id`, game, ROM, title id, sequence, party slot, species). Unimplemented rows print “not implemented” and do not launch Azahar.

## Azahar process

- Launch with `open -a /Applications/Azahar.app --args <rom>` (the inner Mach-O warns if launched directly).
- Wait until the window exists and RPC answers.
- Load the `.3ds` from `resources/`.
- Enable **Emulation → Configuration → Debug → Enable RPC Server**. If the checkbox does not persist (known Azahar bug), the bot must fail with a clear message when UDP 45987 does not reply.
- macOS Accessibility for the app that launches Python (same as Jirachi).
- Ctrl+C stops the bot and **leaves Azahar running**.

## Inputs

`pynput`, focus Azahar, tap a mapped key. Soft reset holds L+R+Start. Dialogue waits are plan 05, not pad timing.

`--probe-inputs`: tap A, B, Start, then L+R+Start with visible delays.

## Poipole cycle (timings TBD in plan 05)

One-time manual setup of the hunt save:

- After Ultra Necrozma, Ultra Megalopolis, Dulse (Moon) / Soliera (Sun).
- Decline Poipole if needed so it can be hunted.
- Empty party slot.
- **Save there.** That save is the SR baseline.

Loop skeleton (delays measured later):

1. Title → Continue (A).
2. Wait for overworld.
3. Talk (A) and mash A through dialogue until **You received Poipole**. Then A (dismiss) → B (decline nickname) → mash A to finish adding it to the party. Do not open the save menu on a fail.
4. Wait until party RAM has species **803** (Poipole).
5. Compute SV.
6. Fail → L+R+Start → back to 1. **Do not open the save menu.**
7. Shiny → menu (X / `Z`) → Save → wait for `main` mtime/size flush → copy to `resources/` → stop.

## Memory / shiny test

RPC `read_memory` on the game process.

Starting party pointer for USUM on Citra (must be **verified on Azahar with this dump**):

- Address: `0x33F7FA44`
- Slot stride: 484 bytes
- After PK7 decrypt: species at `0x08`, TID/SID at `0x0C`/`0x0E`, PID at `0x18`
- Poipole = 803 (`0x0323`)

PK7 decrypt (Gen 6/7): encryption constant at `0x00`, unshuffle four 56-byte blocks, XOR with LCG `seed = seed * 0x41C64E6D + 0x6073`.

Shiny value (Gen 6+):

```
sv = ((pid >> 16) ^ (pid & 0xFFFF) ^ tid ^ sid) & 0xFFFF
shiny iff sv < 16
```

Log **sv** every attempt, not only yes/no. `--parse-sv` reads party RAM via RPC without hunting. It does **not** parse the on-disk `main` (save crypto is not PK7).

If `0x33F7FA44` is wrong (update 1.2, region, Azahar vs Citra): plan 06 scans for a PK7 / species 803 and stores the offset. A `.3ds` cart dump is usually 1.0; confirm no 1.2 update in NAND.

Do **not** write shiny into RAM. Do **not** use cheats.

This hunt does **not** restore a backup `main` on fail (unlike Jirachi). Soft reset reloads the last in-game save. Fail path must never save.

## Logs

Every attempt line is written in **both** places, same content:

- stdout
- append-only UTF-8 `logs/attempts.txt` (gitignore `logs/`)

```
2026-09-20T18:00:00Z  attempt=5  duration_s=42.1  sv=1842  result=fail
```

Resume: last `attempt=N` → next is `N+1`. Persist hunt start in `logs/hunt_started.txt`; do not reset on resume. Resume does **not** continue an in-game attempt.

Shiny extra line (`logs/shiny.txt` + stdout):

```
SHINY  2026-09-20T19:10:00Z  attempts=3759  total_s=123456.7  sv=7  save=resources/main-poipole-shiny-1
```

`result=miss` / `sv=-1` if Poipole never appears (desync). Recovery: extra SR, or relaunch Azahar if stuck (define in plan 09).

## When shiny

1. Do not soft reset.
2. Save in-game. Wait until Azahar’s `main` changes.
3. Copy `main` → `resources/main-poipole-shiny-N` where N is 1 + max existing `main-poipole-shiny-(\d+)`.
4. Log the attempt + summary. `notify_shiny` is a stub (Discord later).
5. Exit 0. A later launch whose last log line is `result=shiny` must **not** touch the save (warn and exit).

Azahar’s live `main` keeps the shiny. `resources/` copies are the incremental archive for a future continuous hunter.

## Loop (happy path)

1. Interactive picker → Poipole.
2. Path check (ROM, Azahar binary). Fail loudly if missing.
3. Launch Azahar with the ROM. Connect RPC.
4. Run the Poipole sequence once.
5. Read party, compute SV, log the attempt.
6. If not shiny: soft reset, go to 4.
7. If shiny: when-shiny path, exit 0.

`--max-attempts N` stops after N logged attempts. `--force-shiny` fakes a hit (copy + logs) without hunting. `--probe-inputs` does not hunt.

## Out of scope (phase 1)

- Real Discord / notifications
- Other hunts (Type: Null, Tapus, Ultra Beasts, …)
- RNG manipulation / 3DSRNGTool
- Cheats or forcing shiny in RAM
- Ultra Sun until a dump exists in `resources/`
- Savestates (in-game save + SR only)
- GUI

## Done when (after 01–09)

`python3 -m botusum` shows the picker, launches Azahar, completes one Poipole cycle, logs `attempt` / `duration_s` / `sv`, soft-resets on fail, and on shiny saves, copies `main-poipole-shiny-N`, logs total time, and exits 0.
