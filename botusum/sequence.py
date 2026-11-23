"""Gift cycles. Hold/wait constants live here, not in __main__."""

from __future__ import annotations

import time

from botusum.inputs import PadDriver

# Measured: 31s mash A from the parked hunt save lands on nickname
# Yes/No (28s + the old tap-A / 1s-A slice folded in). B declines.
# After-B A still tuning. Poipole is not in the party until after B.
MASH_A_DURATION_S = 31.0
MASH_A_AFTER_B_S = 1.0
MASH_A_GAP_S = 0.05

# After the receive sequence: wait, then X, Y, A, A. Overworld mash dropped
# for now (still tuning how long from Poipole received to field).
SAVE_TO_OVERWORLD_WAIT_S = 2.0


class SequenceError(Exception):
    """Poipole sequence missed a window or could not send inputs."""


def run_poipole_sequence(pad: PadDriver) -> int:
    """Receive Poipole through nickname-no. Does not save or soft-reset."""
    print(f"Poipole: mash A for {MASH_A_DURATION_S:.0f}s")
    taps = pad.mash("A", MASH_A_DURATION_S, gap_s=MASH_A_GAP_S)
    print(f"Poipole: mashed A x{taps}")
    print("Poipole: B (decline nickname)")
    pad.tap("B")
    print(f"Poipole: mash A for {MASH_A_AFTER_B_S:.0f}s")
    taps_after = pad.mash("A", MASH_A_AFTER_B_S, gap_s=MASH_A_GAP_S)
    print(f"Poipole: mashed A x{taps_after}")
    return taps + taps_after


# Ancient Poni Path. Soft reset already leaves the game on the title, so
# the boot wait is only the first attempt after Azahar launches.
# Then mash A through the title and the save, and step right onto the
# Wicke/Hau trigger. Circle-pad right is the arrow key, not D-pad H.
# Boot wait and title mash are still short first cuts. The 0.5s wait and
# 40s A end on nickname Yes/No. B declines. Type: Null is not in the party
# until the after-B mash, same length as Poipole's.
TYPE_NULL_BOOT_WAIT_S = 6.0
TYPE_NULL_TITLE_MASH_A_S = 5.0
TYPE_NULL_STEP_HOLD_S = 0.2
TYPE_NULL_AFTER_STEP_S = 0.5
TYPE_NULL_MASH_A_S = 40.0
TYPE_NULL_MASH_A_AFTER_B_S = 1.0
# After the Pokémon is in the party, Wicke's scene continues. The menu
# cannot open until it ends. Unmeasured; long so X is not pressed mid-text.
TYPE_NULL_SHINY_DIALOGUE_MASH_A_S = 20.0
TYPE_NULL_SAVE_GAP_S = 0.5


def run_type_null_sequence(pad: PadDriver, *, boot: bool = False) -> int:
    """Continue the save, step onto the trigger, decline nickname.

    `boot` waits for the ROM to reach the title. Only the first attempt
    after launch sets it. Later attempts follow a soft reset, which is
    already on the title. Does not save or soft-reset.
    """
    if boot:
        print(f"Type: Null: wait {TYPE_NULL_BOOT_WAIT_S:.0f}s for the game to load")
        time.sleep(TYPE_NULL_BOOT_WAIT_S)
    print(f"Type: Null: mash A for {TYPE_NULL_TITLE_MASH_A_S:.1f}s (title, continue save)")
    title_taps = pad.mash("A", TYPE_NULL_TITLE_MASH_A_S, gap_s=MASH_A_GAP_S)
    print(f"Type: Null: mashed A x{title_taps}")
    print(f"Type: Null: circle-pad right for {TYPE_NULL_STEP_HOLD_S:.1f}s")
    pad.hold("CircleRight", hold_s=TYPE_NULL_STEP_HOLD_S)
    print(f"Type: Null: wait {TYPE_NULL_AFTER_STEP_S:.1f}s")
    time.sleep(TYPE_NULL_AFTER_STEP_S)
    print(f"Type: Null: mash A for {TYPE_NULL_MASH_A_S:.0f}s")
    taps = pad.mash("A", TYPE_NULL_MASH_A_S, gap_s=MASH_A_GAP_S)
    print(f"Type: Null: mashed A x{taps}")
    print("Type: Null: B (decline nickname)")
    pad.tap("B")
    print(f"Type: Null: mash A for {TYPE_NULL_MASH_A_AFTER_B_S:.1f}s")
    taps_after = pad.mash("A", TYPE_NULL_MASH_A_AFTER_B_S, gap_s=MASH_A_GAP_S)
    print(f"Type: Null: mashed A x{taps_after}")
    return title_taps + taps + taps_after


def save_type_null(pad: PadDriver) -> None:
    """Finish the post-receive scene, then save. Does not copy `main`."""
    print(
        "Type: Null: mash A for "
        f"{TYPE_NULL_SHINY_DIALOGUE_MASH_A_S:.0f}s (dialogue before save)"
    )
    taps = pad.mash("A", TYPE_NULL_SHINY_DIALOGUE_MASH_A_S, gap_s=MASH_A_GAP_S)
    print(f"Type: Null: mashed A x{taps}")
    print(
        f"Type: Null: X, wait {TYPE_NULL_SAVE_GAP_S:.1f}s, Y, "
        f"wait {TYPE_NULL_SAVE_GAP_S:.1f}s, A, "
        f"wait {TYPE_NULL_SAVE_GAP_S:.1f}s, A (save)"
    )
    pad.play(
        [
            ("X", 0.0),
            ("Y", TYPE_NULL_SAVE_GAP_S),
            ("A", TYPE_NULL_SAVE_GAP_S),
            ("A", TYPE_NULL_SAVE_GAP_S),
        ]
    )


def save_game(pad: PadDriver) -> None:
    """Wait, then X, Y, A, A to save. Does not copy `main`."""
    print(f"Shiny: wait {SAVE_TO_OVERWORLD_WAIT_S:.0f}s (overworld dialogues)")
    time.sleep(SAVE_TO_OVERWORLD_WAIT_S)
    print("Shiny: X, Y, then A, A (save)")
    pad.tap("X")
    pad.tap("Y")
    pad.tap("A")
    pad.tap("A")
