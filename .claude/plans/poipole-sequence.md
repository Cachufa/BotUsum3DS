# 5. Poipole sequence

- **Number:** 05 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Calibrate the in-game gift cycle: title → overworld → talk → receive Poipole. Measure delays; do not guess frames.

## Context

Hunt save (manual, once): Ultra Megalopolis, Dulse (Moon) / Soliera (Sun), Poipole not received, empty party slot, **saved there**. Soft reset reloads that save. Never save on a fail.

Skeleton:

1. Title → Continue (A).
2. Wait for overworld.
3. Talk (A); mash A through dialogue / receive / nickname (keep default).
4. Wait until party has species 803 (depends on plan 06).
5. Fail → L+R+Start → step 1.
6. Shiny → save menu (plan 08).

## Steps

- [ ] Record one manual attempt and write hold/wait constants.
- [ ] Title → Continue → talk → receive.
- [ ] Soft reset back to title.

## Out of scope

SV math, file copy, Discord.

## Done when

One scripted attempt receives Poipole from a parked save and SR returns to the same prompt. Timings are constants in code, not magic sleeps scattered in `__main__`.
