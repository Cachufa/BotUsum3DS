"""Poipole sequence timings (no Azahar, no HID)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from botusum.inputs import PadDriver
from botusum.sequence import (
    MASH_A_AFTER_B_S,
    MASH_A_DURATION_S,
    MASH_A_GAP_S,
    SAVE_TO_OVERWORLD_WAIT_S,
    TYPE_NULL_AFTER_STEP_S,
    TYPE_NULL_BOOT_WAIT_S,
    TYPE_NULL_MASH_A_AFTER_B_S,
    TYPE_NULL_MASH_A_S,
    TYPE_NULL_SAVE_GAP_S,
    TYPE_NULL_SHINY_DIALOGUE_MASH_A_S,
    TYPE_NULL_STEP_HOLD_S,
    TYPE_NULL_TITLE_MASH_A_S,
    run_poipole_sequence,
    run_type_null_sequence,
    save_game,
    save_type_null,
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
        self.holds: list[tuple[str, float]] = []
        self.plays: list[list[tuple[str, float]]] = []

    def tap(self, button: str) -> None:
        self.taps.append(button)

    def mash(self, button: str, duration_s: float, *, gap_s: float) -> int:
        self.calls.append((button, duration_s, gap_s))
        return 17

    def hold(self, *buttons: str, hold_s: float = 0.5) -> None:
        for button in buttons:
            self.holds.append((button, hold_s))

    def play(self, steps: list[tuple[str, float]]) -> None:
        self.plays.append(list(steps))
        for button, _delay in steps:
            self.taps.append(button)


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

    def test_type_null_from_title_skips_boot_wait(self) -> None:
        pad = FakePad()
        with patch("botusum.sequence.time.sleep") as slept:
            taps = run_type_null_sequence(pad)
        self.assertEqual(taps, 51)
        self.assertEqual(
            [call.args[0] for call in slept.call_args_list],
            [TYPE_NULL_AFTER_STEP_S],
        )
        self.assertEqual(TYPE_NULL_BOOT_WAIT_S, 6.0)
        self.assertEqual(TYPE_NULL_TITLE_MASH_A_S, 5.0)
        self.assertEqual(TYPE_NULL_AFTER_STEP_S, 0.5)
        self.assertEqual(TYPE_NULL_MASH_A_S, 40.0)
        self.assertEqual(TYPE_NULL_MASH_A_AFTER_B_S, 1.0)
        self.assertEqual(
            pad.calls,
            [
                ("A", TYPE_NULL_TITLE_MASH_A_S, MASH_A_GAP_S),
                ("A", TYPE_NULL_MASH_A_S, MASH_A_GAP_S),
                ("A", TYPE_NULL_MASH_A_AFTER_B_S, MASH_A_GAP_S),
            ],
        )
        self.assertEqual(pad.holds, [("CircleRight", TYPE_NULL_STEP_HOLD_S)])
        self.assertEqual(pad.taps, ["B"])

    def test_type_null_first_launch_waits_for_boot(self) -> None:
        pad = FakePad()
        with patch("botusum.sequence.time.sleep") as slept:
            run_type_null_sequence(pad, boot=True)
        self.assertEqual(
            [call.args[0] for call in slept.call_args_list],
            [TYPE_NULL_BOOT_WAIT_S, TYPE_NULL_AFTER_STEP_S],
        )

    def test_type_null_shiny_mashes_dialogue_then_saves(self) -> None:
        pad = FakePad()
        with patch("botusum.sequence.time.sleep") as slept:
            save_type_null(pad)
        self.assertEqual(TYPE_NULL_SHINY_DIALOGUE_MASH_A_S, 20.0)
        self.assertEqual(TYPE_NULL_SAVE_GAP_S, 0.5)
        self.assertEqual(
            pad.calls,
            [("A", TYPE_NULL_SHINY_DIALOGUE_MASH_A_S, MASH_A_GAP_S)],
        )
        slept.assert_not_called()
        self.assertEqual(
            pad.plays,
            [[
                ("X", 0.0),
                ("Y", TYPE_NULL_SAVE_GAP_S),
                ("A", TYPE_NULL_SAVE_GAP_S),
                ("A", TYPE_NULL_SAVE_GAP_S),
            ]],
        )

    def test_save_game_x_y_then_two_a(self) -> None:
        pad = FakePad()
        with patch("botusum.sequence.time.sleep") as slept:
            save_game(pad)
        slept.assert_called_once_with(SAVE_TO_OVERWORLD_WAIT_S)
        self.assertEqual(SAVE_TO_OVERWORLD_WAIT_S, 2.0)
        self.assertEqual(pad.calls, [])
        self.assertEqual(pad.taps, ["X", "Y", "A", "A"])

    def test_pad_mash_maps_a_to_session(self) -> None:
        session = FakeSession()
        pad = PadDriver(session)  # type: ignore[arg-type]
        taps = pad.mash("A", 5.0, gap_s=0.05)
        self.assertEqual(taps, 42)
        self.assertEqual(session.calls, [("a", 5.0, None, 0.05)])


if __name__ == "__main__":
    unittest.main()
