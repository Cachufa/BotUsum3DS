# 9. Hunt loop

- **Number:** 09 / 09
- **Status:** in progress
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Wire picker, Azahar, sequence, SV, logs, and when-shiny into `python3 -m botusum`. Repeat until shiny, Ctrl+C, or `--max-attempts`.

## Context

Happy path in the umbrella. Fail: soft reset, no in-game save. Miss (`sv=-1`): extra SR or relaunch Azahar if stuck (pick one and document it).

`--max-attempts N` for tests. Ctrl+C stops the bot, leaves Azahar.

Unlike Jirachi, do **not** restore a backup `main` on fail.

## Steps

- [x] One attempt: sequence then RAM SV (`run_poipole_once`). Save is plan 08. No loop yet.
- [ ] Default command = loop.
- [x] Log every attempt.
- [x] Shiny → plan 08, exit 0.
- [ ] `--max-attempts`.
- [x] Miss: cannot read species 803 → `sv=-1  result=miss` and L+R+Start. `--parse-sv` does not SR.

## Out of scope

Discord, extra hunts.

## Done when

`--max-attempts 1` does picker → Azahar → one cycle → log → SR if fail. A real shiny (or `--force-shiny`) stops with copy + total time.
