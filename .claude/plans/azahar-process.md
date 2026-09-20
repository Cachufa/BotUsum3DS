# 2. Azahar process

- **Number:** 02 / 09
- **Status:** requirements — not started
- **Parent:** [usum-shiny-loop.md](usum-shiny-loop.md)

## Goal

Launch Azahar with the Ultra Moon ROM, wait until it is usable, connect the RPC server. Ctrl+C must not kill Azahar.

## Context

- App: `/Applications/Azahar.app`
- Launch: `open -a /Applications/Azahar.app --args <rom>` (do not run the inner Mach-O; it shows a warning dialog).
- ROM: `resources/Pokemon Ultra Luna.3ds`
- RPC: UDP `127.0.0.1:45987`. Enable **Emulation → Configuration → Debug → Enable RPC Server**. If the setting does not persist, fail clearly when the port does not reply.
- Vendor Azahar’s `citra.py` (read/write memory, process list).

## Steps

- [ ] Launch / reuse Azahar with the ROM.
- [ ] Wait for window + RPC.
- [ ] Ctrl+C leaves Azahar running.
- [ ] Path / RPC errors on stderr, exit `1`.

## Out of scope

Button injection, party parse, hunt loop.

## Done when

A command boots Azahar on the ROM and a Python RPC read succeeds (or fails with a clear RPC-disabled message).
