"""Hunt CLI: `python3 -m botusum` from the repo root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from botusum.azahar import AzaharError, AzaharSession
from botusum.paths import HuntPaths
from botusum.rpc import RPC_HOST, RPC_PORT


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
