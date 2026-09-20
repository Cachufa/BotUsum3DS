# 6. Parse shiny value

- **Number:** 06 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Read the party from Azahar RAM, decrypt PK7, compute shiny value. Log `sv` every attempt.

## Context

RPC `read_memory`. Starting USUM party pointer (Citra; **verify on Azahar**): `0x33F7FA44`, slot stride 484 bytes.

After decrypt: species `0x08`, TID/SID `0x0C`/`0x0E`, PID `0x18`. Poipole = 803.

PK7: EC at `0x00`, unshuffle four 56-byte blocks, XOR LCG `seed = seed * 0x41C64E6D + 0x6073`.

```
sv = ((pid >> 16) ^ (pid & 0xFFFF) ^ tid ^ sid) & 0xFFFF
shiny iff sv < 16
```

If the pointer is wrong: scan for species 803 / PK7 checksum and store the offset. Cart `.3ds` is usually 1.0.

`--parse-sv` reads RAM (or a `main` on disk) without hunting. Do not write RAM. Do not use cheats.

## Steps

- [ ] Vendor/wrap `citra.py`.
- [ ] Decrypt PK7 + SV.
- [ ] Find Poipole in party (species 803).
- [ ] `--parse-sv`.
- [ ] Verify pointer on this dump; scan if needed.

## Out of scope

Inputs, save copy, Discord.

## Done when

With the game open and Poipole in the party, `--parse-sv` prints species, PID, TID, SID, `sv`, and shiny yes/no. Matches a known non-shiny (and a forced test if available).
