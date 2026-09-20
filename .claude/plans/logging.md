# 7. Logging

- **Number:** 07 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Every attempt is logged to **stdout and** `logs/attempts.txt`. Restarting continues `attempt` from the file. Hunt start time is kept for total duration.

## Context

Append-only UTF-8. Gitignore `logs/`. Same line in both sinks. Never truncate on startup.

```
2026-09-20T18:00:00Z  attempt=1  duration_s=42.1  sv=1842  result=fail
```

Resume: last `attempt=N` → next is `N+1`; missing file → 1. Resume does **not** continue an in-game attempt. Persist hunt start (`logs/hunt_started.txt`); do not reset on resume.

`result=miss` / `sv=-1` if Poipole is missing.

Shiny extra file: [when-shiny.md](when-shiny.md).

Mirror `botjirachi/huntlog.py` as needed.

## Steps

- [x] Dual write (print + append).
- [x] Parse last attempt on startup.
- [x] Persist hunt start timestamp.
- [x] Run header optional; no secrets.

## Out of scope

Discord.

## Done when

Kill and rerun: next line is `attempt=N+1`; old lines still in the file; stdout shows the same lines.
