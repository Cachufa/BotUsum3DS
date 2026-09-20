# resources/

Current files (reference only; do not change unless asked):

- `Pokemon Ultra Luna.3ds` (Ultra Moon dump; copy or symlink)

Shiny archives written by the bot (gitignored):

- `main-poipole-shiny-N`

Rules:

- Treat dumps as opaque binaries.
- `.3ds` / `.cci` / `.cia` / `main` / `main-*` under `resources/` are gitignored. Do not force-add them.
- Do not overwrite the live Azahar `main` except via in-game save (shiny path) or when the user asks.
- Fail path: never save in-game; never copy a non-shiny `main` into `resources/`.
- In the plan, document which dump is used (Ultra Moon vs Ultra Sun) and the Title ID.
