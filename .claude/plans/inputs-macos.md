# 3. Inputs (macOS)

- **Number:** 03 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Send 3DS buttons to Azahar from Python on macOS: focus the window, tap/hold mapped keys, soft reset.

## Context

`pynput`. Accessibility required for the app that launches the bot.

Default Azahar keyboard map:

| 3DS | Key |
|-----|-----|
| A | A |
| B | S |
| X | Z |
| Y | X |
| L | Q |
| R | W |
| Start | M |
| Select | N |
| D-pad | T / G / F / H |

Soft reset: hold L+R+Start (`Q`+`W`+`M`). Hold/gap times configurable.

`--probe-inputs`: tap A, B, Start, then L+R+Start with visible delays.

## Steps

- [ ] Focus Azahar before sending keys.
- [ ] Tap / hold helpers.
- [ ] Soft-reset chord.
- [ ] `--probe-inputs`.

## Out of scope

Dialogue timings, RAM, hunt loop.

## Done when

`--probe-inputs` is visible in Azahar (A/B/Start/SR) with the default map.
