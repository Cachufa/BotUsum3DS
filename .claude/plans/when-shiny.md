# 8. When shiny

- **Number:** 08 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

On SV &lt; 16: save in-game, copy Azahar’s `main` to `resources/main-poipole-shiny-N`, log summary, stop. Do not soft reset.

## Context

1. Menu (X / `Z`) → Save. Wait for `main` mtime/size flush.
2. Copy to `resources/main-poipole-shiny-N` (N = 1 + max existing).
3. Attempt line `result=shiny` + `logs/shiny.txt`:

```
SHINY  2026-09-20T19:10:00Z  attempts=3759  total_s=123456.7  sv=7  save=resources/main-poipole-shiny-1
```

4. `notify_shiny` stub (Discord later).
5. Exit 0. Later launch with last `result=shiny` must not touch the save.

Live Azahar `main` keeps the shiny. `resources/` copies are the incremental archive.

`--force-shiny` fakes this path without hunting.

## Steps

- [ ] In-game save + wait for flush.
- [ ] Incremental copy.
- [ ] Summary log + stub notify.
- [ ] Skip hunt if last result is shiny.
- [ ] `--force-shiny`.

## Out of scope

Real Discord, other species filenames (use poipole in the name for now).

## Done when

`--force-shiny` writes `main-poipole-shiny-1` then `-2` on a second run, logs summary, exit 0. A following default launch refuses to hunt.
