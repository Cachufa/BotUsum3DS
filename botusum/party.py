"""Read the USUM party from Azahar RAM via RPC and find a species.

Does not parse the on-disk `main` save (that uses save crypto, not PK7).
"""

from __future__ import annotations

from dataclasses import dataclass

from botusum.paths import ULTRA_MOON_TITLE_ID
from botusum.pk7 import PK7_STORED, Pk7, Pk7Error, parse_pk7
from botusum.rpc import RpcClient, RpcError

# Citra/Azahar USUM party (verify with --parse-sv on this dump).
USUM_PARTY_ADDRESS = 0x33F7FA44
PARTY_SLOT_STRIDE = 484
PARTY_SLOTS = 6
POIPOLE_SPECIES = 803
ULTRA_MOON_TITLE_ID_INT = int(ULTRA_MOON_TITLE_ID, 16)

# First scan window if the stock pointer has no matching species.
SCAN_START = 0x33E00000
SCAN_END = 0x34080000
SCAN_PAGE = 0x4000


class PartyError(Exception):
    """Party RAM could not be read, or the species is not in the party."""


@dataclass(frozen=True)
class PartyMon:
    slot: int
    address: int
    pk7: Pk7

    @property
    def species(self) -> int:
        return self.pk7.species

    @property
    def pid(self) -> int:
        return self.pk7.pid

    @property
    def tid(self) -> int:
        return self.pk7.tid

    @property
    def sid(self) -> int:
        return self.pk7.sid

    @property
    def sv(self) -> int:
        return self.pk7.sv

    @property
    def shiny(self) -> bool:
        return self.pk7.shiny


def attach_game(
    client: RpcClient,
    title_id: int = ULTRA_MOON_TITLE_ID_INT,
) -> tuple[int, str]:
    """Select the Ultra Moon process so read_memory hits game RAM."""
    try:
        processes = client.process_list()
    except RpcError as exc:
        raise PartyError(str(exc)) from exc
    for proc_id, (tid, name) in processes.items():
        if tid == title_id:
            try:
                client.set_process(proc_id)
            except RpcError as exc:
                raise PartyError(str(exc)) from exc
            return proc_id, name
    raise PartyError(
        "Ultra Moon is not running in Azahar "
        f"(title {title_id:016X}). Load the ROM and try again."
    )


def _slot_from_bytes(raw: bytes, *, slot: int, address: int) -> PartyMon | None:
    if len(raw) < PK7_STORED:
        return None
    stored = raw[:PK7_STORED]
    if stored == b"\x00" * PK7_STORED:
        return None
    try:
        pk7 = parse_pk7(stored)
    except Pk7Error:
        return None
    return PartyMon(slot=slot, address=address, pk7=pk7)


def read_party(
    client: RpcClient,
    *,
    base: int = USUM_PARTY_ADDRESS,
) -> list[PartyMon | None]:
    size = PARTY_SLOT_STRIDE * PARTY_SLOTS
    try:
        blob = client.read_memory(base, size)
    except RpcError as exc:
        raise PartyError(str(exc)) from exc
    if len(blob) < size:
        raise PartyError(
            f"RPC read_memory at 0x{base:08X} returned {len(blob)} bytes, need {size}"
        )
    slots: list[PartyMon | None] = []
    for i in range(PARTY_SLOTS):
        start = i * PARTY_SLOT_STRIDE
        slots.append(
            _slot_from_bytes(
                blob[start : start + PK7_STORED],
                slot=i,
                address=base + start,
            )
        )
    return slots


def find_species(
    slots: list[PartyMon | None],
    species: int,
) -> PartyMon:
    for mon in slots:
        if mon is not None and mon.species == species:
            return mon
    raise PartyError(f"species {species} is not in the party")


def scan_for_species(
    client: RpcClient,
    species: int,
    *,
    start: int = SCAN_START,
    end: int = SCAN_END,
) -> PartyMon | None:
    """Walk a RAM window for a checksum-valid PK7 of `species`."""
    overlap = PK7_STORED - 4
    address = start
    while address < end:
        try:
            blob = client.read_memory(address, min(SCAN_PAGE, end - address))
        except RpcError:
            address += SCAN_PAGE
            continue
        if len(blob) >= PK7_STORED:
            for offset in range(0, len(blob) - PK7_STORED + 1, 4):
                try:
                    pk7 = parse_pk7(blob[offset : offset + PK7_STORED])
                except Pk7Error:
                    continue
                if pk7.species == species:
                    return PartyMon(slot=-1, address=address + offset, pk7=pk7)
        if len(blob) < SCAN_PAGE:
            break
        address += SCAN_PAGE - overlap
    return None


def locate_species(
    client: RpcClient,
    species: int,
    *,
    base: int = USUM_PARTY_ADDRESS,
    scan: bool = True,
    scan_start: int = SCAN_START,
    scan_end: int = SCAN_END,
) -> tuple[int, list[PartyMon | None], PartyMon]:
    """Return (party base, slots, matching mon). Scans RAM if needed."""
    slots = read_party(client, base=base)
    try:
        mon = find_species(slots, species)
        return base, slots, mon
    except PartyError:
        if not scan:
            raise
    found = scan_for_species(client, species, start=scan_start, end=scan_end)
    if found is None:
        raise PartyError(
            f"species {species} not at 0x{base:08X} and not in "
            f"scan 0x{scan_start:08X}-0x{scan_end:08X}"
        )
    return found.address, slots, found


def format_mon(mon: PartyMon) -> str:
    shiny = "yes" if mon.shiny else "no"
    return (
        f"species={mon.species}  pid=0x{mon.pid:08X}  "
        f"tid={mon.tid}  sid={mon.sid}  sv={mon.sv}  shiny={shiny}"
    )


def format_slot(mon: PartyMon | None, index: int) -> str:
    if mon is None:
        return f"slot={index}  empty"
    return f"slot={index}  address=0x{mon.address:08X}  {format_mon(mon)}"
