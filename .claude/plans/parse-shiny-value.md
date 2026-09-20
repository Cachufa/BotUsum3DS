# 6. Parse shiny value

- **Number:** 06 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Read the party from Azahar RAM, decrypt PK7, compute shiny value. Log `sv` every attempt.

## Context

RPC `read_memory` on the **game process**, not the on-disk `main` save. BotJirachiGC parses a Gen 3 `.sav`; USUM party in RAM is already a PK7 (encrypted with PK7 crypto only). Save-file AES / block layout is out of scope.

Starting USUM party pointer (Citra; **verify on Azahar**): `0x33F7FA44`, slot stride 484 bytes. Stored PK7 is 232 bytes per slot.

Plan 05: 31s mash A lands on nickname Yes/No; B declines. Species 803 is **not** in the party until after that, plus a 1s after-B A mash (tuning). Read SV after that; do not mash into the save menu on a fail.

After decrypt: species `0x08`, TID/SID `0x0C`/`0x0E`, PID `0x18`. Poipole = 803.

PK7: EC at `0x00`, unshuffle four 56-byte blocks, XOR LCG `seed = seed * 0x41C64E6D + 0x6073`.

```
sv = ((pid >> 16) ^ (pid & 0xFFFF) ^ tid ^ sid) & 0xFFFF
shiny iff sv < 16
```

If the pointer is wrong: scan `0x33E00000`–`0x34080000` for species 803 / PK7 checksum and print the offset. Cart `.3ds` is usually 1.0.

`--parse-sv` attaches to Azahar RPC and reads party RAM without hunting. Do not write RAM. Do not use cheats. Do not parse `main`.

## Steps

- [x] Vendor/wrap `citra.py` (`botusum/rpc.py`; `set_process` selects Ultra Moon).
- [x] Decrypt PK7 + SV (`botusum/pk7.py`).
- [x] Find Poipole in party (species 803) (`botusum/party.py`).
- [x] `--parse-sv` (skips picker and hunt).
- [x] Hunt path: after the Poipole sequence, `run_poipole_once` calls the same RAM SV read.
- [x] Verify pointer on this dump with Poipole in party (`0x33F7FA44`; hunt read species 803 after the gift sequence).

## Out of scope

Inputs, save copy, Discord, on-disk SAV7 `main`.

## Done when

With the game open and Poipole in the party, `--parse-sv` prints species, PID, TID, SID, `sv`, and shiny yes/no. Matches a known non-shiny (and a forced test if available).
