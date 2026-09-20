"""Hunt CLI: `python3 -m botusum` from the repo root."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from botusum.azahar import AzaharError, AzaharSession
from botusum.huntlog import HuntLog, result_for_sv
from botusum.inputs import PROBE_PAUSE_S, InputError, PadDriver
from botusum.party import (
    POIPOLE_SPECIES,
    USUM_PARTY_ADDRESS,
    PartyError,
    PartyMon,
    attach_game,
    format_mon,
    format_slot,
    locate_species,
)
from botusum.paths import HuntPaths
from botusum.picker import HuntSpec, PickerError, select_hunt
from botusum.rpc import RPC_HOST, RPC_PORT, RpcClient, RpcError
from botusum.sequence import SequenceError, run_poipole_sequence, save_game
from botusum.shiny import (
    FORCE_SHINY_SV,
    ShinyError,
    file_fingerprint,
    handle_shiny,
    wait_for_main_flush,
)


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
    parser.add_argument(
        "--parse-sv",
        action="store_true",
        help="Read party RAM via RPC, decrypt PK7, print SV (no hunt)",
    )
    parser.add_argument(
        "--force-shiny",
        action="store_true",
        help=(
            "Fake a shiny hit. Alone: copy Azahar main to "
            "resources/main-poipole-shiny-N without hunting. "
            "With --hunt: one receive then in-game save (X, Y, A, A)"
        ),
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
    if args.force_shiny and args.hunt is None:
        return run_force_shiny(paths)
    hunt: HuntSpec | None = None
    skip_picker = args.probe_inputs or args.parse_sv
    if not skip_picker:
        hunt_log = HuntLog(paths.logs_dir)
        if hunt_log.last_logged_result() == "shiny" and not args.force_shiny:
            print(
                "Shiny already logged; not hunting. "
                f"See {hunt_log.shiny_path}",
                file=sys.stderr,
            )
            return 0
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
    missing = paths.missing()
    if missing:
        report_missing(missing)
        return 1
    print_header(paths)
    session = AzaharSession(paths)
    try:
        reused, titles, client, processes = session.ensure_ready()
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
    if args.parse_sv:
        try:
            return parse_sv(client)
        except KeyboardInterrupt:
            print("Interrupted; leaving Azahar running", file=sys.stderr)
            return 130
    if hunt is not None:
        try:
            return run_selected_hunt(
                session, hunt, client, force_save=args.force_shiny,
            )
        except KeyboardInterrupt:
            print("Interrupted; leaving Azahar running", file=sys.stderr)
            return 130
    return 0


def read_party_sv(
    client: RpcClient,
    species: int,
) -> tuple[int, list[PartyMon | None], PartyMon]:
    proc_id, name = attach_game(client)
    print(f"RPC process pid={proc_id} name={name}")
    print(
        f"Reading party RAM at 0x{USUM_PARTY_ADDRESS:08X} "
        "(PK7 decrypt, not the on-disk save)"
    )
    return locate_species(client, species)


def print_party_sv(
    base: int,
    slots: list[PartyMon | None],
    mon: PartyMon,
    species: int,
) -> None:
    for index, slot in enumerate(slots):
        print(f"  {format_slot(slot, index)}")
    if base != USUM_PARTY_ADDRESS:
        print(
            f"Stock pointer 0x{USUM_PARTY_ADDRESS:08X} had no species {species}; "
            f"found PK7 at 0x{mon.address:08X}"
        )
    print(format_mon(mon))
    print(f"address=0x{mon.address:08X}  slot={mon.slot}  checksum=ok")


def parse_sv(client: RpcClient, species: int = POIPOLE_SPECIES) -> int:
    try:
        base, slots, mon = read_party_sv(client, species)
    except (PartyError, RpcError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print_party_sv(base, slots, mon, species)
    return 0


def log_attempt(
    hunt_log: HuntLog | None,
    *,
    attempt: int | None,
    started_at: float | None,
    sv: int,
    result: str | None = None,
) -> None:
    if hunt_log is None or attempt is None or started_at is None:
        return
    hunt_log.write_attempt(
        attempt=attempt,
        duration_s=time.perf_counter() - started_at,
        sv=sv,
        result=result,
    )


def run_poipole_once(
    pad: PadDriver,
    client: RpcClient,
    species: int,
    hunt_log: HuntLog | None = None,
    paths: HuntPaths | None = None,
    force_save: bool = False,
) -> int:
    """Receive Poipole, then read SV. Miss: sv=-1 and soft reset. Shiny: save."""
    attempt = hunt_log.next_attempt_number() if hunt_log is not None else None
    started_at = time.perf_counter() if hunt_log is not None else None
    run_poipole_sequence(pad)
    try:
        base, slots, mon = read_party_sv(client, species)
    except (PartyError, RpcError) as exc:
        print(str(exc), file=sys.stderr)
        log_attempt(hunt_log, attempt=attempt, started_at=started_at, sv=-1)
        if hunt_log is None:
            print("sv=-1  result=miss")
        print("Soft reset (L+R+Start)")
        pad.soft_reset()
        return 1
    print_party_sv(base, slots, mon, species)
    result = result_for_sv(mon.sv)
    take_save = result == "shiny" or force_save
    if (
        hunt_log is not None
        and paths is not None
        and attempt is not None
        and started_at is not None
        and take_save
    ):
        duration_s = time.perf_counter() - started_at
        if force_save and result != "shiny":
            print("Force save: in-game save after receive (timing test)")
        try:
            before = file_fingerprint(paths.ultra_moon_main)
            save_game(pad)
            wait_for_main_flush(paths.ultra_moon_main, before)
        except (SequenceError, ShinyError, OSError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if result == "shiny":
            return handle_shiny(
                hunt_log,
                attempt=attempt,
                duration_s=duration_s,
                sv=mon.sv,
                live_main=paths.ultra_moon_main,
                resources_dir=paths.resources_dir,
                repo_root=paths.repo_root,
            )
        print(
            "Force save: in-game save done. Restore the parked hunt save "
            "before hunting again.",
            file=sys.stderr,
        )
    log_attempt(hunt_log, attempt=attempt, started_at=started_at, sv=mon.sv)
    return 0


def run_selected_hunt(
    session: AzaharSession,
    hunt: HuntSpec,
    client: RpcClient,
    force_save: bool = False,
) -> int:
    if hunt.sequence != "poipole":
        print(f"{hunt.name} is not implemented.", file=sys.stderr)
        return 1
    species = hunt.species if hunt.species is not None else POIPOLE_SPECIES
    hunt_log = HuntLog(session.paths.logs_dir)
    started, next_attempt = hunt_log.prepare()
    hunt_log.write_run_header(started, next_attempt)
    try:
        pad = PadDriver(session)
        return run_poipole_once(
            pad, client, species, hunt_log, session.paths,
            force_save=force_save,
        )
    except (AzaharError, InputError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def run_force_shiny(paths: HuntPaths) -> int:
    """Shiny path without hunting or Azahar. Copies the live `main` as-is."""
    hunt_log = HuntLog(paths.logs_dir)
    started, next_attempt = hunt_log.prepare()
    hunt_log.write_run_header(started, next_attempt)
    print("Force shiny: skipping hunt and Azahar")
    try:
        return handle_shiny(
            hunt_log,
            attempt=next_attempt,
            duration_s=0.0,
            sv=FORCE_SHINY_SV,
            live_main=paths.ultra_moon_main,
            resources_dir=paths.resources_dir,
            repo_root=paths.repo_root,
        )
    except ShinyError as exc:
        print(str(exc), file=sys.stderr)
        return 1


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
