"""Hunt loop: fail SR, miss SR, shiny stop, --max-attempts (no Azahar)."""

from __future__ import annotations

import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from botusum.__main__ import build_parser, run_selected_hunt
from botusum.huntlog import HuntLog
from botusum.party import USUM_PARTY_ADDRESS
from botusum.paths import HuntPaths
from botusum.picker import HUNTS
from botusum.pk7 import build_pk7, encrypt_pk7
from botusum.rpc import RpcError
from botusum.shiny import file_fingerprint

from tests.test_party import FakePad, MemoryRpc, _party_blob


def _paths(root: Path) -> HuntPaths:
    return HuntPaths(
        repo_root=root,
        ultra_moon_rom=root / "missing.3ds",
        azahar_app=root / "Azahar.app",
        azahar_user_dir=root / "azahar-user",
    )


def _write_live_main(paths: HuntPaths, data: bytes = b"parked") -> Path:
    path = paths.ultra_moon_main
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _encrypted(*, pid: int, tid: int, sid: int) -> bytes:
    return encrypt_pk7(
        build_pk7(
            species=803,
            pid=pid,
            tid=tid,
            sid=sid,
            encryption_constant=0x55,
        )
    )


# sv = ((pid >> 16) ^ (pid & 0xFFFF) ^ tid ^ sid); 0 is shiny, others fail.
FAIL_PK7 = _encrypted(pid=0x11112222, tid=10, sid=20)
SHINY_PK7 = _encrypted(pid=0x00010000, tid=1, sid=0)


class CyclingRpc(MemoryRpc):
    """New party blob on each `set_process` (one hunt attempt)."""

    def __init__(self, blobs: list[bytes], base: int) -> None:
        super().__init__(blobs[0], base)
        self._blobs = blobs
        self._index = -1

    def set_process(self, process_id: int) -> None:
        super().set_process(process_id)
        self._index += 1
        self.blob = self._blobs[min(self._index, len(self._blobs) - 1)]


def _session(paths: HuntPaths) -> MagicMock:
    session = MagicMock()
    session.paths = paths
    return session


class MaxAttemptsFlagTests(unittest.TestCase):
    def test_parser_accepts_max_attempts(self) -> None:
        args = build_parser().parse_args(["--hunt", "poipole", "--max-attempts", "1"])
        self.assertEqual(args.max_attempts, 1)
        self.assertEqual(args.hunt, "poipole")

    def test_rejects_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    MemoryRpc(_party_blob(), USUM_PARTY_ADDRESS),  # type: ignore[arg-type]
                    max_attempts=0,
                    pad=FakePad(),  # type: ignore[arg-type]
                )
            self.assertEqual(code, 1)
            self.assertIn("--max-attempts must be >= 1", stderr.getvalue())


class HuntLoopTests(unittest.TestCase):
    def test_fail_then_shiny_soft_resets_once(self) -> None:
        client = CyclingRpc(
            [_party_blob(FAIL_PK7), _party_blob(SHINY_PK7)],
            USUM_PARTY_ADDRESS,
        )
        pad = FakePad()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            live = _write_live_main(paths)

            def _flush(path: Path, _before, **_kwargs):
                path.write_bytes(b"shiny-saved")
                return file_fingerprint(path)

            with (
                patch("botusum.__main__.wait_for_main_flush", side_effect=_flush),
                patch("botusum.sequence.time.sleep"),
            ):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    client,  # type: ignore[arg-type]
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 1)
            self.assertEqual(
                [t for t in pad.taps if t != "B"],
                ["X", "Y", "A", "A"],
            )
            hunt_log = HuntLog(paths.logs_dir)
            attempts = hunt_log.attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=fail", attempts)
            self.assertIn("result=shiny", attempts)
            self.assertTrue((root / "resources" / "main-poipole-shiny-1").is_file())
            self.assertEqual(live.read_bytes(), b"shiny-saved")

    def test_max_attempts_stops_after_fails(self) -> None:
        client = CyclingRpc(
            [_party_blob(FAIL_PK7), _party_blob(FAIL_PK7), _party_blob(SHINY_PK7)],
            USUM_PARTY_ADDRESS,
        )
        pad = FakePad()
        stdout = io.StringIO()
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            _write_live_main(paths)
            with patch("sys.stdout", stdout), patch("botusum.sequence.time.sleep"):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    client,  # type: ignore[arg-type]
                    max_attempts=2,
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 2)
            self.assertNotIn("X", pad.taps)
            hunt_log = HuntLog(paths.logs_dir)
            attempts = hunt_log.attempts_path.read_text(encoding="utf-8")
            self.assertEqual(attempts.count("result=fail"), 2)
            self.assertNotIn("result=shiny", attempts)
            self.assertIn("Stopped after 2 attempt(s) (--max-attempts)", stdout.getvalue())
            self.assertFalse((Path(tmp) / "resources" / "main-poipole-shiny-1").exists())

    def test_max_attempts_one_soft_resets_on_fail(self) -> None:
        client = MemoryRpc(_party_blob(FAIL_PK7), USUM_PARTY_ADDRESS)
        pad = FakePad()
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            with patch("sys.stdout", io.StringIO()):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    client,  # type: ignore[arg-type]
                    max_attempts=1,
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 1)
            attempts = HuntLog(paths.logs_dir).attempts_path.read_text(encoding="utf-8")
            self.assertEqual(attempts.count("result=fail"), 1)

    def test_miss_then_shiny_does_not_double_reset_on_miss(self) -> None:
        client = CyclingRpc(
            [_party_blob(), _party_blob(SHINY_PK7)],
            USUM_PARTY_ADDRESS,
        )
        pad = FakePad()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            _write_live_main(paths)

            def _flush(path: Path, _before, **_kwargs):
                path.write_bytes(b"shiny-saved")
                return file_fingerprint(path)

            with (
                patch("botusum.__main__.wait_for_main_flush", side_effect=_flush),
                patch("botusum.sequence.time.sleep"),
            ):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    client,  # type: ignore[arg-type]
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            # Miss SR inside run_poipole_once; no extra loop SR. Shiny does not SR.
            self.assertEqual(pad.resets, 1)
            hunt_log = HuntLog(paths.logs_dir)
            attempts = hunt_log.attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=miss", attempts)
            self.assertIn("result=shiny", attempts)

    def test_force_save_does_not_loop(self) -> None:
        client = CyclingRpc(
            [_party_blob(FAIL_PK7), _party_blob(SHINY_PK7)],
            USUM_PARTY_ADDRESS,
        )
        pad = FakePad()
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            live = _write_live_main(paths)

            def _flush(path: Path, _before, **_kwargs):
                path.write_bytes(b"timing-saved")
                return file_fingerprint(path)

            with (
                patch("botusum.__main__.wait_for_main_flush", side_effect=_flush),
                patch("botusum.sequence.time.sleep"),
            ):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    client,  # type: ignore[arg-type]
                    force_save=True,
                    max_attempts=5,
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 0)
            self.assertEqual(len(pad.calls), 2)
            self.assertEqual(live.read_bytes(), b"timing-saved")
            attempts = HuntLog(paths.logs_dir).attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=fail", attempts)
            self.assertNotIn("result=shiny", attempts)


class RpcErrorCountsAsMissTests(unittest.TestCase):
    def test_rpc_error_logs_miss_and_honors_max_attempts(self) -> None:
        class BoomRpc(MemoryRpc):
            def read_memory(self, address: int, size: int) -> bytes:
                raise RpcError("udp timeout")

        pad = FakePad()
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            with patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()):
                code = run_selected_hunt(
                    _session(paths),
                    HUNTS[0],
                    BoomRpc(_party_blob(FAIL_PK7), USUM_PARTY_ADDRESS),  # type: ignore[arg-type]
                    max_attempts=1,
                    pad=pad,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 1)
            attempts = HuntLog(paths.logs_dir).attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=miss", attempts)


if __name__ == "__main__":
    unittest.main()
