"""Party RAM reader (fake RPC memory; no Azahar, no on-disk save)."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from botusum.__main__ import build_parser, run_poipole_once
from botusum.huntlog import HuntLog
from botusum.party import (
    PARTY_SLOT_STRIDE,
    PARTY_SLOTS,
    ULTRA_MOON_TITLE_ID_INT,
    USUM_PARTY_ADDRESS,
    PartyError,
    find_species,
    locate_species,
    read_party,
    scan_for_species,
)
from botusum.pk7 import PK7_STORED, build_pk7, encrypt_pk7
from botusum.rpc import RpcError


class MemoryRpc:
    def __init__(self, blob: bytes, base: int) -> None:
        self.blob = blob
        self.base = base
        self.selected: int | None = None

    def process_list(self) -> dict[int, tuple[int, str]]:
        return {1: (ULTRA_MOON_TITLE_ID_INT, "momiji")}

    def set_process(self, process_id: int) -> None:
        self.selected = process_id

    def read_memory(self, address: int, size: int) -> bytes:
        offset = address - self.base
        if offset < 0 or offset >= len(self.blob):
            raise RpcError(f"unmapped 0x{address:08X}")
        return self.blob[offset : offset + size]


def _party_blob(*encrypted_slots: bytes | None, extra: bytes = b"") -> bytes:
    blob = bytearray(PARTY_SLOT_STRIDE * PARTY_SLOTS)
    for i, slot in enumerate(encrypted_slots):
        if slot is None:
            continue
        start = i * PARTY_SLOT_STRIDE
        blob[start : start + len(slot)] = slot
    return bytes(blob) + extra


class PartyRamTests(unittest.TestCase):
    def test_reads_poipole_in_slot_zero(self) -> None:
        plain = build_pk7(
            species=803,
            pid=0x11112222,
            tid=10,
            sid=20,
            encryption_constant=0xABCDEF01,
        )
        encrypted = encrypt_pk7(plain)
        ram = _party_blob(encrypted)
        client = MemoryRpc(ram, USUM_PARTY_ADDRESS)
        slots = read_party(client, base=USUM_PARTY_ADDRESS)
        mon = find_species(slots, 803)
        self.assertEqual(mon.slot, 0)
        self.assertEqual(mon.address, USUM_PARTY_ADDRESS)
        self.assertEqual(mon.species, 803)
        self.assertEqual(mon.pid, 0x11112222)
        self.assertEqual(mon.tid, 10)
        self.assertEqual(mon.sid, 20)
        self.assertFalse(mon.shiny)

    def test_finds_poipole_in_later_slot(self) -> None:
        pika = encrypt_pk7(
            build_pk7(
                species=25,
                pid=1,
                tid=1,
                sid=1,
                encryption_constant=0x10,
            )
        )
        poipole = encrypt_pk7(
            build_pk7(
                species=803,
                pid=0x00010000,
                tid=1,
                sid=0,
                encryption_constant=0x20,
            )
        )
        ram = _party_blob(pika, None, poipole)
        client = MemoryRpc(ram, USUM_PARTY_ADDRESS)
        slots = read_party(client, base=USUM_PARTY_ADDRESS)
        self.assertEqual(slots[1], None)
        mon = find_species(slots, 803)
        self.assertEqual(mon.slot, 2)
        self.assertTrue(mon.shiny)

    def test_missing_species(self) -> None:
        ram = _party_blob()
        client = MemoryRpc(ram, USUM_PARTY_ADDRESS)
        slots = read_party(client, base=USUM_PARTY_ADDRESS)
        with self.assertRaises(PartyError):
            find_species(slots, 803)

    def test_scan_finds_pk7_off_the_stock_pointer(self) -> None:
        poipole = encrypt_pk7(
            build_pk7(
                species=803,
                pid=0xDEADBEEF,
                tid=7,
                sid=9,
                encryption_constant=0x33333333,
            )
        )
        padding = b"\x00" * 0x80
        ram = padding + poipole
        base = 0x33E00000
        client = MemoryRpc(ram, base)
        found = scan_for_species(
            client,
            803,
            start=base,
            end=base + len(ram),
        )
        assert found is not None
        self.assertEqual(found.address, base + 0x80)
        self.assertEqual(found.pid, 0xDEADBEEF)
        self.assertEqual(found.species, 803)

    def test_locate_scans_when_stock_pointer_is_empty(self) -> None:
        poipole = encrypt_pk7(
            build_pk7(
                species=803,
                pid=42,
                tid=1,
                sid=2,
                encryption_constant=0x44,
            )
        )
        # Stock party region is empty; PK7 sits later in the same blob.
        empty = _party_blob()
        gap = b"\x00" * 0x100
        ram = empty + gap + poipole
        client = MemoryRpc(ram, USUM_PARTY_ADDRESS)
        _base, slots, mon = locate_species(
            client,
            803,
            base=USUM_PARTY_ADDRESS,
            scan=True,
            scan_start=USUM_PARTY_ADDRESS,
            scan_end=USUM_PARTY_ADDRESS + len(ram),
        )
        self.assertTrue(all(slot is None for slot in slots))
        self.assertEqual(mon.pid, 42)
        self.assertEqual(
            mon.address,
            USUM_PARTY_ADDRESS + PARTY_SLOT_STRIDE * PARTY_SLOTS + 0x100,
        )
        self.assertGreaterEqual(len(poipole), PK7_STORED)


class ParseSvFlagTests(unittest.TestCase):
    def test_parse_sv_flag(self) -> None:
        args = build_parser().parse_args(["--parse-sv"])
        self.assertTrue(args.parse_sv)
        self.assertFalse(args.probe_inputs)


class FakePad:
    def __init__(self) -> None:
        self.taps: list[str] = []
        self.calls: list[tuple[str, float, float]] = []
        self.resets = 0

    def tap(self, button: str) -> None:
        self.taps.append(button)

    def mash(self, button: str, duration_s: float, *, gap_s: float) -> int:
        self.calls.append((button, duration_s, gap_s))
        return 3

    def soft_reset(self, hold_s: float | None = None) -> None:
        self.resets += 1


class ReceiveAndParseTests(unittest.TestCase):
    def test_sequence_then_sv(self) -> None:
        poipole = encrypt_pk7(
            build_pk7(
                species=803,
                pid=0x00010000,
                tid=1,
                sid=0,
                encryption_constant=0x55,
            )
        )
        client = MemoryRpc(_party_blob(poipole), USUM_PARTY_ADDRESS)
        pad = FakePad()
        code = run_poipole_once(pad, client, 803)  # type: ignore[arg-type]
        self.assertEqual(code, 0)
        self.assertEqual(pad.taps, ["B"])
        self.assertEqual(len(pad.calls), 2)
        self.assertEqual(client.selected, 1)
        self.assertEqual(pad.resets, 0)

    def test_miss_prints_sv_minus_one_and_soft_resets(self) -> None:
        client = MemoryRpc(_party_blob(), USUM_PARTY_ADDRESS)
        pad = FakePad()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run_poipole_once(pad, client, 803)  # type: ignore[arg-type]
        self.assertEqual(code, 1)
        self.assertEqual(pad.resets, 1)
        self.assertIn("sv=-1  result=miss", stdout.getvalue())

    def test_miss_dual_writes_attempt_line(self) -> None:
        client = MemoryRpc(_party_blob(), USUM_PARTY_ADDRESS)
        pad = FakePad()
        stdout = io.StringIO()
        with TemporaryDirectory() as tmp:
            hunt_log = HuntLog(Path(tmp), stdout=stdout)
            hunt_log.prepare()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_poipole_once(
                    pad, client, 803, hunt_log,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 1)
            self.assertEqual(pad.resets, 1)
            self.assertEqual(hunt_log.next_attempt_number(), 2)
            line = hunt_log.attempts_path.read_text(encoding="utf-8").strip()
            self.assertIn("attempt=1", line)
            self.assertIn("sv=-1", line)
            self.assertIn("result=miss", line)
            self.assertEqual(stdout.getvalue().splitlines()[-1], line)


if __name__ == "__main__":
    unittest.main()

