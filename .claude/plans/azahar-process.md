# 2. Azahar process

- **Number:** 02 / 09
- **Status:** done
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Launch Azahar with the Ultra Moon ROM, wait until it is usable, connect the RPC server. Ctrl+C must not kill Azahar.

## Context

- App: `/Applications/Azahar.app`
- Launch: `open -a /Applications/Azahar.app --args <rom>` (do not run the inner Mach-O; it shows a warning dialog).
- ROM: `resources/Pokemon Ultra Luna.3ds`
- RPC: UDP `127.0.0.1:45987`. Before a fresh launch, set `[Debugging] enable_rpc_server=true` and `enable_rpc_server\default=false` in `qt-config.ini` (Azahar ignores the value while `\default=true`). If UDP 45987 still does not reply, fail clearly.
- Vendor Azahar’s `citra.py` (read/write memory, process list) as `botusum/citra.py`.

## Steps

- [x] Launch / reuse Azahar with the ROM.
- [x] Wait for window + RPC.
- [x] Ctrl+C leaves Azahar running.
- [x] Path / RPC errors on stderr, exit `1`.

## Out of scope

Button injection, party parse, hunt loop.

## Done when

A command boots Azahar on the ROM and a Python RPC read succeeds (or fails with a clear RPC-disabled message).
