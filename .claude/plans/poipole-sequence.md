# 5. Poipole sequence

- **Number:** 05 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Calibrate the in-game gift cycle: title → overworld → talk → receive Poipole. Measure delays; do not guess frames.

## Context

Hunt save (manual, once): Ultra Megalopolis, Dulse (Moon) / Soliera (Sun), Poipole not received, empty party slot, **saved there**. Soft reset reloads that save. Never save on a fail.

Skeleton:

1. Title → Continue (A).
2. Wait for overworld.
3. Talk (A); mash A through dialogue until **You received Poipole**.
4. Poipole is **not** in the party at that box. Mash A 31s through receive onto nickname Yes/No → B (decline nickname) → mash A 1s after B (tuning). Then wait until party has species 803 (plan 06).
5. Fail → L+R+Start → step 1. Stop after the post-nickname A mash; do not open the save menu.
6. Shiny → extra A / save menu (plan 08). Nickname-no is already in this sequence.

## Steps

- [x] Mash A for 31s (`MASH_A_DURATION_S` / `MASH_A_GAP_S` in `botusum/sequence.py`; `PadDriver.mash` focuses once). Folded the old tap-A + 1s-A-before-B into this mash.
- [x] Recorded: 32s overshot nickname; 31s is the nickname Yes/No window. Species 803 is **not** in the party yet.
- [x] Then tap B (no nickname) → mash A 1s (`MASH_A_AFTER_B_S`, still tuning).
- [x] After that slice, hunt reads party RAM and prints SV (`run_poipole_once`). No SR / save yet.
- [x] Title → Continue stays folded into the 31s mash (calibrated; not a separate wait).
- [x] Soft reset on miss is hunt-loop (`sv=-1` → L+R+Start), not a second sequence here.

## Out of scope

SV math, file copy, Discord.

## Done when

One scripted attempt receives Poipole from a parked save and SR returns to the same prompt. Timings are constants in code, not magic sleeps scattered in `__main__`.
