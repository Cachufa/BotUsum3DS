"""Poipole sequence timings (no Azahar, no HID)."""

from __future__ import annotations

import unittest

from botusum.inputs import PadDriver
from botusum.sequence import (
    MASH_A_AFTER_B_S,
    MASH_A_DURATION_S,
    MASH_A_GAP_S,
    run_poipole_sequence,
)


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float, float | None, float]] = []

    def mash_key(
        self,
        key: str,
        duration_s: float,
        *,
        hold_s: float | None = None,
        gap_s: float = 0.05,
    ) -> int:
        self.calls.append((key, duration_s, hold_s, gap_s))
        return 42


class FakePad:
    def __init__(self) -> None:
        self.taps: list[str] = []
        self.calls: list[tuple[str, float, float]] = []

    def tap(self, button: str) -> None:
        self.taps.append(button)

    def mash(self, button: str, duration_s: float, *, gap_s: float) -> int:
        self.calls.append((button, duration_s, gap_s))
        return 17


class SequenceTests(unittest.TestCase):
    def test_mash_a_then_nickname_b(self) -> None:
        pad = FakePad()
        taps = run_poipole_sequence(pad)
        self.assertEqual(taps, 34)
        self.assertEqual(pad.taps, ["B"])
        self.assertEqual(
            pad.calls,
            [
                ("A", MASH_A_DURATION_S, MASH_A_GAP_S),
                ("A", MASH_A_AFTER_B_S, MASH_A_GAP_S),
            ],
        )
        self.assertEqual(MASH_A_DURATION_S, 31.0)
        self.assertEqual(MASH_A_AFTER_B_S, 1.0)

    def test_pad_mash_maps_a_to_session(self) -> None:
        session = FakeSession()
        pad = PadDriver(session)  # type: ignore[arg-type]
        taps = pad.mash("A", 5.0, gap_s=0.05)
        self.assertEqual(taps, 42)
        self.assertEqual(session.calls, [("a", 5.0, None, 0.05)])


if __name__ == "__main__":
    unittest.main()
