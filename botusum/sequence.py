"""Poipole gift cycle. Hold/wait constants live here, not in __main__."""

from __future__ import annotations

from botusum.inputs import PadDriver

# Measured: 31s mash A from the parked hunt save lands on nickname
# Yes/No (28s + the old tap-A / 1s-A slice folded in). B declines.
# After-B A still tuning. Poipole is not in the party until after B.
MASH_A_DURATION_S = 31.0
MASH_A_AFTER_B_S = 1.0
MASH_A_GAP_S = 0.05


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
