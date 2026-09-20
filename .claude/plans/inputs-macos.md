# 3. Inputs (macOS)

- **Number:** 03 / 09
- **Status:** done
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

Soft reset: hold L+R+Start (`Q`+`W`+`M`). A tap is a press/release; no inter-key gap (that was a Jirachi leftover). Dialogue waits belong in plan 05.

`--probe-inputs`: tap A, B, Start, then L+R+Start with visible delays.

## Steps

- [x] Focus Azahar before sending keys.
- [x] Tap / hold helpers.
- [x] Soft-reset chord.
- [x] `--probe-inputs`.

## Out of scope

Dialogue timings, RAM, hunt loop.

## Done when

`--probe-inputs` is visible in Azahar (A/B/Start/SR) with the default map.
