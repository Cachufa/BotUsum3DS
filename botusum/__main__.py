"""Hunt CLI: `python3 -m botusum` from the repo root."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from botusum.azahar import AzaharError, AzaharSession
from botusum.inputs import PROBE_PAUSE_S, InputError, PadDriver
from botusum.paths import HuntPaths
from botusum.picker import HuntSpec, PickerError, select_hunt
from botusum.rpc import RPC_HOST, RPC_PORT
from botusum.sequence import run_poipole_sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="botusum",
        description="Shiny hunt Pokémon Ultra Sun / Ultra Moon in Azahar.",
    )
    parser.add_argument("--rom", type=Path, help="Ultra Moon .3ds / .cci")
    parser.add_argument("--azahar", type=Path, help="Azahar.app or azahar executable")
    parser.add_argument(
        "--azahar-user-dir",
        type=Path,
        help="Azahar user data directory",
    )
    parser.add_argument(
        "--probe-inputs",
        action="store_true",
        help="After Azahar boots: tap A, B, Start, then L+R+Start (soft reset)",
    )
    parser.add_argument(
        "--hunt",
        metavar="ID",
        help="Skip the picker (poipole, or a list number)",
    )
    return parser


def resolve_paths(args: argparse.Namespace) -> HuntPaths:
    return HuntPaths.defaults(
        ultra_moon_rom=args.rom,
        azahar_app=args.azahar,
        azahar_user_dir=args.azahar_user_dir,
    )


def report_missing(missing: list[tuple[str, Path]]) -> None:
    print("Missing required paths:", file=sys.stderr)
    for label, path in missing:
        print(f"  {label}: {path}", file=sys.stderr)


def print_header(paths: HuntPaths) -> None:
    print("BotUsum3DS — required paths found")
    print(f"  repo:   {paths.repo_root}")
    print(f"  rom:    {paths.ultra_moon_rom}")
    print(f"  azahar: {paths.azahar_app}")
    print(f"  user:   {paths.azahar_user_dir}")
    print(f"  save:   {paths.ultra_moon_main}")
    print(f"  logs:   {paths.logs_dir}")
    print(f"  config: {paths.qt_config}")


def print_rpc_ok(
    reused: bool,
    titles: list[str],
    processes: dict[int, tuple[int, str]],
) -> None:
    action = "reused" if reused else "launched"
    print(f"Azahar {action}; RPC {RPC_HOST}:{RPC_PORT} answered")
    for title in titles:
        print(f"  window: {title}")
    if not processes:
        print("  rpc process list: (empty; game may still be booting)")
        return
    for proc_id, (title_id, name) in processes.items():
        print(f"  rpc pid={proc_id} title={title_id:016X} name={name}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    hunt: HuntSpec | None = None
    if not args.probe_inputs:
        try:
            hunt = select_hunt(args.hunt)
        except KeyboardInterrupt:
            print("Interrupted", file=sys.stderr)
            return 130
        except PickerError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if not hunt.implemented:
            print(f"{hunt.name} is not implemented.", file=sys.stderr)
            return 1
        print(f"Hunt: {hunt.name}  ({hunt.summary})")
    paths = resolve_paths(args)
    missing = paths.missing()
    if missing:
        report_missing(missing)
        return 1
    print_header(paths)
    session = AzaharSession(paths)
    try:
        reused, titles, _client, processes = session.ensure_ready()
    except KeyboardInterrupt:
        print("Interrupted; leaving Azahar running", file=sys.stderr)
        return 130
    except AzaharError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print_rpc_ok(reused, titles, processes)
    if args.probe_inputs:
        try:
            return probe_inputs(session)
        except KeyboardInterrupt:
            print("Interrupted; leaving Azahar running", file=sys.stderr)
            return 130
    if hunt is not None:
        try:
            return run_selected_hunt(session, hunt)
        except KeyboardInterrupt:
            print("Interrupted; leaving Azahar running", file=sys.stderr)
            return 130
    return 0


def run_selected_hunt(session: AzaharSession, hunt: HuntSpec) -> int:
    if hunt.sequence != "poipole":
        print(f"{hunt.name} is not implemented.", file=sys.stderr)
        return 1
    try:
        pad = PadDriver(session)
        run_poipole_sequence(pad)
    except (AzaharError, InputError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def probe_inputs(session: AzaharSession) -> int:
    try:
        pad = PadDriver(session)
        print(
            "Input map: "
            f"A={pad.button_map['A']!r} "
            f"B={pad.button_map['B']!r} "
            f"Start={pad.button_map['Start']!r} "
            f"L={pad.button_map['L']!r} "
            f"R={pad.button_map['R']!r}"
        )
        print("Focus Azahar, tap A")
        pad.tap("A")
        time.sleep(PROBE_PAUSE_S)
        print("Tap B")
        pad.tap("B")
        time.sleep(PROBE_PAUSE_S)
        print("Tap Start")
        pad.tap("Start")
        time.sleep(PROBE_PAUSE_S)
        print("Soft reset (L+R+Start)")
        pad.soft_reset()
    except (AzaharError, InputError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Input probe sent. Windows:")
    for title in session.window_titles():
        print(f"  window: {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
