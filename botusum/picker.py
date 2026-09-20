"""Terminal hunt list. Phase 1: Poipole is the only live hunt."""

from __future__ import annotations

import sys
import termios
import tty
from dataclasses import dataclass
from typing import TextIO

from botusum.paths import ULTRA_MOON_ROM_NAME, ULTRA_MOON_TITLE_ID

POIPOLE_SPECIES = 803
TYPE_NULL_SPECIES = 772


class PickerError(Exception):
    """Invalid hunt choice, cancelled list, or no TTY."""


@dataclass(frozen=True)
class HuntSpec:
    id: str
    name: str
    summary: str
    game: str
    title_id: str
    rom_name: str
    species: int | None
    party_slot: int | None
    sequence: str | None
    implemented: bool


HUNTS: tuple[HuntSpec, ...] = (
    HuntSpec(
        id="poipole",
        name="Poipole",
        summary="Ultra Megalopolis gift, 1/4096",
        game="Ultra Moon",
        title_id=ULTRA_MOON_TITLE_ID,
        rom_name=ULTRA_MOON_ROM_NAME,
        species=POIPOLE_SPECIES,
        party_slot=0,
        sequence="poipole",
        implemented=True,
    ),
    HuntSpec(
        id="type-null",
        name="Type: Null",
        summary="Aether Paradise gift",
        game="Ultra Moon",
        title_id=ULTRA_MOON_TITLE_ID,
        rom_name=ULTRA_MOON_ROM_NAME,
        species=TYPE_NULL_SPECIES,
        party_slot=0,
        sequence=None,
        implemented=False,
    ),
)


def format_row(index: int, hunt: HuntSpec, *, current: bool | None = None) -> str:
    body = f"[{index}] {hunt.name}  ({hunt.summary})"
    if current is None:
        return body
    mark = ">" if current else " "
    return f"{mark} {body}"


def format_list(hunts: tuple[HuntSpec, ...] = HUNTS, *, current: int | None = None) -> str:
    lines = [
        format_row(i, hunt, current=None if current is None else current == i)
        for i, hunt in enumerate(hunts, start=1)
    ]
    return "\n".join(lines)


def resolve_choice(choice: str, hunts: tuple[HuntSpec, ...] = HUNTS) -> HuntSpec:
    text = choice.strip()
    if not text:
        raise PickerError(_unknown_message(choice, hunts))
    if text.isdigit():
        index = int(text)
        if 1 <= index <= len(hunts):
            return hunts[index - 1]
        raise PickerError(_unknown_message(choice, hunts))
    key = text.lower()
    for hunt in hunts:
        if hunt.id == key:
            return hunt
    raise PickerError(_unknown_message(choice, hunts))


def _unknown_message(choice: str, hunts: tuple[HuntSpec, ...]) -> str:
    ids = ", ".join(hunt.id for hunt in hunts)
    shown = choice.strip() or "(empty)"
    return f"Unknown hunt {shown!r}. Choose a list number or id ({ids})."


def select_hunt(
    choice: str | None = None,
    *,
    hunts: tuple[HuntSpec, ...] = HUNTS,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> HuntSpec:
    """Resolve --hunt, or show the list (arrows / number + Enter)."""
    if choice is not None and str(choice).strip() != "":
        return resolve_choice(str(choice), hunts)
    if stdin.isatty() and stdout.isatty():
        try:
            return _pick_interactive(hunts, stdin=stdin, stdout=stdout)
        except (termios.error, OSError):
            return _pick_line(hunts, stdin=stdin, stdout=stdout)
    return _pick_line(hunts, stdin=stdin, stdout=stdout)


def _pick_line(
    hunts: tuple[HuntSpec, ...],
    *,
    stdin: TextIO,
    stdout: TextIO,
) -> HuntSpec:
    stdout.write("Select a hunt:\n")
    stdout.write(format_list(hunts) + "\n")
    stdout.flush()
    if stdin.isatty():
        stdout.write("Number: ")
        stdout.flush()
    line = stdin.readline()
    if not line:
        raise PickerError("No TTY for the hunt list; pass --hunt poipole")
    return resolve_choice(line, hunts)


def _pick_interactive(
    hunts: tuple[HuntSpec, ...],
    *,
    stdin: TextIO,
    stdout: TextIO,
) -> HuntSpec:
    index = 0
    header = "Select a hunt (↑/↓ or number, Enter; q to quit):"
    _draw(stdout, header, hunts, index, first=True)
    while True:
        key = _read_key(stdin)
        if key in {"\x03"}:
            raise KeyboardInterrupt
        if key in {"q", "Q", "\x1b"}:
            raise PickerError("Cancelled")
        if key in {"\r", "\n"}:
            return hunts[index]
        if key in {"\x1b[A", "k"}:
            index = (index - 1) % len(hunts)
        elif key in {"\x1b[B", "j"}:
            index = (index + 1) % len(hunts)
        elif len(key) == 1 and key.isdigit() and key != "0":
            choice = int(key)
            if 1 <= choice <= len(hunts):
                index = choice - 1
            else:
                continue
        else:
            continue
        _draw(stdout, header, hunts, index, first=False)


def _draw(
    stdout: TextIO,
    header: str,
    hunts: tuple[HuntSpec, ...],
    index: int,
    *,
    first: bool,
) -> None:
    block = header + "\n" + format_list(hunts, current=index + 1)
    lines = block.count("\n") + 1
    if not first:
        stdout.write(f"\x1b[{lines}A\r\x1b[J")
    stdout.write(block + "\n")
    stdout.flush()


def _read_key(stdin: TextIO) -> str:
    fd = stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = stdin.read(1)
        if ch == "\x1b":
            rest = stdin.read(2)
            return ch + rest
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
