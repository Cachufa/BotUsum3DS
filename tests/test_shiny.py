"""Unit tests for the when-shiny path (temp dirs; no ROM dumps)."""

from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from botusum.__main__ import main, run_force_shiny, run_poipole_once
from botusum.huntlog import HuntLog, parse_utc
from botusum.paths import HuntPaths
from botusum.party import USUM_PARTY_ADDRESS
from botusum.pk7 import build_pk7, encrypt_pk7
from botusum.shiny import (
    FORCE_SHINY_SV,
    ShinyError,
    file_fingerprint,
    handle_shiny,
    next_shiny_archive,
    wait_for_main_flush,
)

from tests.test_party import MemoryRpc, _party_blob


def _paths(root: Path) -> HuntPaths:
    return HuntPaths(
        repo_root=root,
        ultra_moon_rom=root / "missing.3ds",
        azahar_app=root / "Azahar.app",
        azahar_user_dir=root / "azahar-user",
    )


def _write_live_main(paths: HuntPaths, data: bytes = b"azahar-main") -> Path:
    path = paths.ultra_moon_main
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


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


class NextArchiveTests(unittest.TestCase):
    def test_starts_at_one_then_increments(self) -> None:
        with TemporaryDirectory() as tmp:
            resources = Path(tmp) / "resources"
            first = next_shiny_archive(resources)
            self.assertEqual(first.name, "main-poipole-shiny-1")
            resources.mkdir()
            first.write_bytes(b"one")
            (resources / "notes.txt").write_text("ignore", encoding="utf-8")
            (resources / "main-poipole-shiny-7").write_bytes(b"seven")
            self.assertEqual(
                next_shiny_archive(resources).name,
                "main-poipole-shiny-8",
            )


class HandleShinyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.paths = _paths(self.root)
        self.stdout = io.StringIO()
        self.log = HuntLog(self.root / "logs", stdout=self.stdout)
        self.log.ensure_hunt_started(
            now=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        )
        self.live = _write_live_main(self.paths)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_copies_archive_and_keeps_live_main(self) -> None:
        when = datetime(2026, 9, 20, 20, 15, tzinfo=timezone.utc)
        with patch("botusum.shiny.notify_shiny") as notify:
            code = handle_shiny(
                self.log,
                attempt=3759,
                duration_s=42.1,
                sv=7,
                live_main=self.live,
                resources_dir=self.paths.resources_dir,
                repo_root=self.root,
                when=when,
            )
        self.assertEqual(code, 0)
        dest = (self.root / "resources" / "main-poipole-shiny-1").resolve()
        self.assertEqual(dest.read_bytes(), b"azahar-main")
        self.assertEqual(self.live.read_bytes(), b"azahar-main")
        notify.assert_called_once()
        kwargs = notify.call_args.kwargs
        self.assertEqual(kwargs["attempt"], 3759)
        self.assertEqual(kwargs["sv"], 7)
        self.assertEqual(kwargs["save_path"].resolve(), dest)
        self.assertAlmostEqual(kwargs["total_s"], 29700.0)

        attempt_line = (
            "2026-09-20T20:15:00Z  attempt=3759  "
            "duration_s=42.1  sv=7  result=shiny"
        )
        summary = (
            "SHINY  2026-09-20T20:15:00Z  attempts=3759  "
            "total_s=29700.0  sv=7  save=resources/main-poipole-shiny-1"
        )
        self.assertEqual(self.stdout.getvalue().splitlines(), [attempt_line, summary])
        self.assertEqual(
            self.log.attempts_path.read_text(encoding="utf-8").splitlines(),
            [attempt_line],
        )
        self.assertEqual(
            self.log.shiny_path.read_text(encoding="utf-8").splitlines(),
            [summary],
        )

    def test_second_copy_uses_next_n(self) -> None:
        handle_shiny(
            self.log,
            attempt=1,
            duration_s=1.0,
            sv=0,
            live_main=self.live,
            resources_dir=self.paths.resources_dir,
            repo_root=self.root,
        )
        self.live.write_bytes(b"second")
        handle_shiny(
            self.log,
            attempt=2,
            duration_s=1.0,
            sv=7,
            live_main=self.live,
            resources_dir=self.paths.resources_dir,
            repo_root=self.root,
        )
        first = self.root / "resources" / "main-poipole-shiny-1"
        second = self.root / "resources" / "main-poipole-shiny-2"
        self.assertEqual(first.read_bytes(), b"azahar-main")
        self.assertEqual(second.read_bytes(), b"second")

    def test_missing_live_main_raises(self) -> None:
        missing = self.root / "no-such-main"
        with self.assertRaises(ShinyError):
            handle_shiny(
                self.log,
                attempt=1,
                duration_s=0.0,
                sv=0,
                live_main=missing,
                resources_dir=self.paths.resources_dir,
                repo_root=self.root,
            )
        self.assertFalse((self.root / "logs" / "attempts.txt").is_file())


class FlushTests(unittest.TestCase):
    def test_returns_when_mtime_or_size_changes(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "main"
            path.write_bytes(b"before")
            before = file_fingerprint(path)
            path.write_bytes(b"after-save")
            got = wait_for_main_flush(
                path, before, timeout_s=1.0, poll_s=0.0, stable_s=0.0,
            )
            self.assertEqual(got, file_fingerprint(path))
            self.assertNotEqual(got, before)

    def test_timeout_if_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "main"
            path.write_bytes(b"same")
            before = file_fingerprint(path)
            with self.assertRaises(ShinyError):
                wait_for_main_flush(
                    path, before, timeout_s=0.0, poll_s=0.0, stable_s=0.0,
                )


class ForceShinyCliTests(unittest.TestCase):
    def test_run_force_shiny_copies_and_skips_azahar(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            live = _write_live_main(paths, b"keep-me")
            with patch("botusum.__main__.AzaharSession") as session:
                code = run_force_shiny(paths)
            self.assertEqual(code, 0)
            session.assert_not_called()
            self.assertEqual(live.read_bytes(), b"keep-me")
            dest = root / "resources" / "main-poipole-shiny-1"
            self.assertEqual(dest.read_bytes(), b"keep-me")
            attempts = (root / "logs" / "attempts.txt").read_text(encoding="utf-8")
            summary = (root / "logs" / "shiny.txt").read_text(encoding="utf-8")
            self.assertIn("result=shiny", attempts)
            self.assertIn(f"sv={FORCE_SHINY_SV}", attempts)
            self.assertTrue(summary.startswith("SHINY  "))
            self.assertIn("save=resources/main-poipole-shiny-1", summary)
            started = (root / "logs" / "hunt_started.txt").read_text(encoding="utf-8")
            self.assertIsNotNone(parse_utc(started))

    def test_force_shiny_second_run_writes_dash_two(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            _write_live_main(paths, b"keep-me")
            self.assertEqual(run_force_shiny(paths), 0)
            self.assertEqual(run_force_shiny(paths), 0)
            self.assertTrue((root / "resources" / "main-poipole-shiny-1").is_file())
            self.assertTrue((root / "resources" / "main-poipole-shiny-2").is_file())

    def test_main_skips_hunt_if_last_attempt_was_shiny(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            live = _write_live_main(paths, b"keep-me")
            HuntLog(paths.logs_dir).write_attempt(
                attempt=3759,
                duration_s=1.0,
                sv=7,
            )
            with (
                patch("botusum.__main__.resolve_paths", return_value=paths),
                patch("botusum.__main__.select_hunt") as picker,
                patch("botusum.__main__.AzaharSession") as session,
            ):
                code = main([])
            self.assertEqual(code, 0)
            picker.assert_not_called()
            session.assert_not_called()
            self.assertEqual(live.read_bytes(), b"keep-me")

    def test_main_force_shiny_does_not_boot_azahar(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            _write_live_main(paths, b"keep-me")
            with (
                patch("botusum.__main__.resolve_paths", return_value=paths),
                patch("botusum.__main__.AzaharSession") as session,
            ):
                code = main(["--force-shiny"])
            self.assertEqual(code, 0)
            session.assert_not_called()
            self.assertTrue((root / "logs" / "shiny.txt").is_file())
            self.assertTrue((root / "resources" / "main-poipole-shiny-1").is_file())

    def test_force_shiny_missing_main_exits_one(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = _paths(Path(tmp))
            code = run_force_shiny(paths)
            self.assertEqual(code, 1)
            self.assertFalse((Path(tmp) / "resources" / "main-poipole-shiny-1").exists())


class LiveShinyAttemptTests(unittest.TestCase):
    def test_shiny_sv_saves_copies_and_does_not_soft_reset(self) -> None:
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
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            live = _write_live_main(paths, b"parked")
            hunt_log = HuntLog(paths.logs_dir, stdout=io.StringIO())
            hunt_log.prepare()
            before = file_fingerprint(live)

            def _flush(path: Path, _before, **_kwargs):
                path.write_bytes(b"shiny-saved")
                return file_fingerprint(path)

            with (
                patch("botusum.__main__.wait_for_main_flush", side_effect=_flush),
                patch("botusum.sequence.time.sleep"),
            ):
                code = run_poipole_once(
                    pad, client, 803, hunt_log, paths,  # type: ignore[arg-type]
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 0)
            self.assertEqual(
                [t for t in pad.taps if t != "B"],
                ["X", "Y", "A", "A"],
            )
            dest = root / "resources" / "main-poipole-shiny-1"
            self.assertEqual(dest.read_bytes(), b"shiny-saved")
            self.assertNotEqual(file_fingerprint(live), before)
            attempts = hunt_log.attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=shiny", attempts)
            self.assertIn("save=resources/main-poipole-shiny-1", hunt_log.shiny_path.read_text(encoding="utf-8"))

    def test_force_save_after_fail_sv_does_not_log_shiny(self) -> None:
        poipole = encrypt_pk7(
            build_pk7(
                species=803,
                pid=0x11112222,
                tid=10,
                sid=20,
                encryption_constant=0xABCDEF01,
            )
        )
        client = MemoryRpc(_party_blob(poipole), USUM_PARTY_ADDRESS)
        pad = FakePad()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _paths(root)
            live = _write_live_main(paths, b"parked")
            hunt_log = HuntLog(paths.logs_dir, stdout=io.StringIO())
            hunt_log.prepare()

            def _flush(path: Path, _before, **_kwargs):
                path.write_bytes(b"timing-saved")
                return file_fingerprint(path)

            with (
                patch("botusum.__main__.wait_for_main_flush", side_effect=_flush),
                patch("botusum.sequence.time.sleep"),
            ):
                code = run_poipole_once(
                    pad, client, 803, hunt_log, paths,  # type: ignore[arg-type]
                    force_save=True,
                )
            self.assertEqual(code, 0)
            self.assertEqual(pad.resets, 0)
            self.assertEqual(
                [t for t in pad.taps if t != "B"],
                ["X", "Y", "A", "A"],
            )
            self.assertEqual(live.read_bytes(), b"timing-saved")
            attempts = hunt_log.attempts_path.read_text(encoding="utf-8")
            self.assertIn("result=fail", attempts)
            self.assertFalse(hunt_log.shiny_path.exists())


if __name__ == "__main__":
    unittest.main()
