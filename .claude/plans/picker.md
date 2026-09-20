# 4. Picker

- **Number:** 04 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Interactive terminal list of hunts. Phase 1: Poipole only.

## Context

```
[1] Poipole  (Ultra Megalopolis gift, 1/4096)
```

Number or arrows + Enter. Each hunt is a registry row: `id`, game, ROM, title id, sequence, party slot, species. Unimplemented rows print “not implemented” and do not launch Azahar.

No GUI.

## Steps

- [x] Registry with Poipole as the only live hunt.
- [x] Interactive select (stdlib first).
- [x] Skip picker if a flag selects the hunt (optional, for tests).

## Out of scope

Implementing other hunts, emulator, RAM.

## Done when

`python3 -m botusum` shows the list, choosing Poipole continues, any other row is rejected clearly.
