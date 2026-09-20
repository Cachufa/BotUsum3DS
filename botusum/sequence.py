"""Poipole gift cycle. Hold/wait constants live here, not in __main__."""

from __future__ import annotations

from botusum.inputs import PadDriver

# Measured: 10s mash A from the parked hunt save lands on the
# "You received Poipole" box. Party should already have species 803.
# Extra A (nickname / dismiss / save menu) is plan 08, not here.
MASH_A_DURATION_S = 10.0
MASH_A_GAP_S = 0.05


class SequenceError(Exception):
    """Poipole sequence missed a window or could not send inputs."""


def run_poipole_sequence(pad: PadDriver) -> int:
    """Mash A until the received-Poipole box. Does not save or soft-reset."""
    print(f"Poipole: mash A for {MASH_A_DURATION_S:.0f}s")
    taps = pad.mash("A", MASH_A_DURATION_S, gap_s=MASH_A_GAP_S)
    print(f"Poipole: mashed A x{taps}")
    return taps
