# Toolchain

- Language: **Python 3.10+**, stdlib first.
- Hunt command (repo root): `python3 -m botusum`
- Optional path overrides: `--rom`, `--azahar`, `--azahar-user-dir`
- Missing Ultra Moon ROM or Azahar.app: print all missing paths on stderr and exit `1`
- Launch Azahar with `open -a Azahar.app --args <rom>`. Do not run `Azahar.app/Contents/MacOS/azahar` directly (macOS warning dialog). Ctrl+C does not kill Azahar.
- RPC: UDP `127.0.0.1:45987`. Enable Debug → Enable RPC Server. Fail clearly if it does not answer.
- Extra deps: `pynput` (keyboard to Azahar). Default 3DS map: A=`A`, B=`S`, X=`Z`, Y=`X`, L=`Q`, R=`W`, Start=`M`, Select=`N`, D-pad T/G/F/H. Soft reset = L+R+Start (`Q`+`W`+`M`).
- Accessibility: System Settings → Privacy & Security → Accessibility → Terminal / Python / the app that launches the bot.
- venv: optional; `.venv/` is gitignored. Homebrew Python blocks `pip3 install` (PEP 668); use a venv for `pynput`.
- Default `python3 -m botusum`: picker → Poipole hunt loop until SV &lt; 16. Fail: soft reset, do not save. Shiny: in-game save, copy `resources/main-poipole-shiny-N`, log summary, exit `0`. `--probe-inputs`, `--parse-sv`, `--force-shiny`, `--max-attempts` as in the umbrella.
- Poipole National Dex 803. Shiny iff SV &lt; 16 (Gen 6+).
- Detail: `.claude/plans/usum-shiny-loop.md`
