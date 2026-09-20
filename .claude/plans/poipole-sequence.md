# 5. Poipole sequence

- **Number:** 05 / 09
- **Status:** in progress
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Calibrate the in-game gift cycle: title → overworld → talk → receive Poipole. Measure delays; do not guess frames.

## Context

Hunt save (manual, once): Ultra Megalopolis, Dulse (Moon) / Soliera (Sun), Poipole not received, empty party slot, **saved there**. Soft reset reloads that save. Never save on a fail.

Skeleton:

1. Title → Continue (A).
2. Wait for overworld.
3. Talk (A); mash A through dialogue until **You received Poipole**.
4. Wait until party has species 803 (plan 06). At the receive box, Poipole should already be in the party.
5. Fail → L+R+Start → step 1. **Do not mash further** (that would leave the receive box and risk a save).
6. Shiny → extra A / nickname / save menu (plan 08).

## Steps

- [x] Mash A for 10s (`MASH_A_DURATION_S` / `MASH_A_GAP_S` in `botusum/sequence.py`; `PadDriver.mash` focuses once).
- [x] Recorded: 10s mash from the parked save stops on the received-Poipole box; party should already have 803. Extra taps for nickname/save are plan 08.
- [ ] Title → Continue as a separate wait (currently folded into the 10s mash).
- [ ] Soft reset back to title.

## Out of scope

SV math, file copy, Discord.

## Done when

One scripted attempt receives Poipole from a parked save and SR returns to the same prompt. Timings are constants in code, not magic sleeps scattered in `__main__`.
