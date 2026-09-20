# 9. Hunt loop

- **Number:** 09 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Wire picker, Azahar, sequence, SV, logs, and when-shiny into `python3 -m botusum`. Repeat until shiny, Ctrl+C, or `--max-attempts`.

## Context

Happy path in the umbrella. Fail: soft reset, no in-game save. Miss (`sv=-1`): extra SR or relaunch Azahar if stuck (pick one and document it).

`--max-attempts N` for tests. Ctrl+C stops the bot, leaves Azahar.

Unlike Jirachi, do **not** restore a backup `main` on fail.

## Steps

- [ ] Default command = loop.
- [ ] Log every attempt.
- [ ] Shiny → plan 08, exit 0.
- [ ] `--max-attempts`.
- [ ] Miss recovery.

## Out of scope

Discord, extra hunts.

## Done when

`--max-attempts 1` does picker → Azahar → one cycle → log → SR if fail. A real shiny (or `--force-shiny`) stops with copy + total time.
