"""PK7 (Gen 6/7) decrypt and shiny value. Operates on RAM blobs, not a save file."""

from __future__ import annotations

import struct
from dataclasses import dataclass

PK7_STORED = 232
PK7_BLOCK = 56
PK7_BLOCKS = 4
SHINY_SV_LIMIT = 16
NATIONAL_DEX_MAX = 807

# PKHeX PokeCrypto.BlockPosition: dest block i comes from source order[i].
_BLOCK_POSITION: tuple[tuple[int, int, int, int], ...] = (
    (0, 1, 2, 3),
    (0, 1, 3, 2),
    (0, 2, 1, 3),
    (0, 3, 1, 2),
    (0, 2, 3, 1),
    (0, 3, 2, 1),
    (1, 0, 2, 3),
    (1, 0, 3, 2),
    (2, 0, 1, 3),
    (3, 0, 1, 2),
    (2, 0, 3, 1),
    (3, 0, 2, 1),
    (1, 2, 0, 3),
    (1, 3, 0, 2),
    (2, 1, 0, 3),
    (3, 1, 0, 2),
    (2, 3, 0, 1),
    (3, 2, 0, 1),
    (1, 2, 3, 0),
    (1, 3, 2, 0),
    (2, 1, 3, 0),
    (3, 1, 2, 0),
    (2, 3, 1, 0),
    (3, 2, 1, 0),
)

_LCG_MULT = 0x41C64E6D
_LCG_ADD = 0x6073


class Pk7Error(Exception):
    """PK7 blob is too short, empty, or checksum-invalid after decrypt."""


@dataclass(frozen=True)
class Pk7:
    encryption_constant: int
    species: int
    tid: int
    sid: int
    pid: int
    checksum: int
    checksum_ok: bool

    @property
    def sv(self) -> int:
        return shiny_value(self.pid, self.tid, self.sid)

    @property
    def shiny(self) -> bool:
        return is_shiny(self.sv)


def shiny_value(pid: int, tid: int, sid: int) -> int:
    return ((pid >> 16) ^ (pid & 0xFFFF) ^ tid ^ sid) & 0xFFFF


def is_shiny(sv: int) -> bool:
    return sv < SHINY_SV_LIMIT


def pk7_checksum(data: bytes) -> int:
    total = 0
    for offset in range(8, PK7_STORED, 2):
        total = (total + int.from_bytes(data[offset : offset + 2], "little")) & 0xFFFF
    return total


def _crypt(data: bytearray, start: int, end: int, seed: int) -> None:
    for offset in range(start, end, 2):
        seed = (seed * _LCG_MULT + _LCG_ADD) & 0xFFFFFFFF
        xor = seed >> 16
        data[offset] ^= xor & 0xFF
        data[offset + 1] ^= (xor >> 8) & 0xFF


def _unshuffle(blocks: bytes, sv: int) -> bytes:
    order = _BLOCK_POSITION[sv % 24]
    out = bytearray(PK7_BLOCK * PK7_BLOCKS)
    for dest, src in enumerate(order):
        src_at = src * PK7_BLOCK
        dest_at = dest * PK7_BLOCK
        out[dest_at : dest_at + PK7_BLOCK] = blocks[src_at : src_at + PK7_BLOCK]
    return bytes(out)


def _shuffle(blocks: bytes, sv: int) -> bytes:
    order = _BLOCK_POSITION[sv % 24]
    out = bytearray(PK7_BLOCK * PK7_BLOCKS)
    for dest, src in enumerate(order):
        src_at = dest * PK7_BLOCK
        dest_at = src * PK7_BLOCK
        out[dest_at : dest_at + PK7_BLOCK] = blocks[src_at : src_at + PK7_BLOCK]
    return bytes(out)


def decrypt_pk7(blob: bytes) -> bytes:
    """Decrypt a 232-byte stored PK7 (party stats are unused for SV)."""
    if len(blob) < PK7_STORED:
        raise Pk7Error(f"PK7 blob is {len(blob)} bytes; need {PK7_STORED}")
    stored = bytearray(blob[:PK7_STORED])
    if stored == b"\x00" * PK7_STORED:
        raise Pk7Error("empty PK7 slot")
    ec = int.from_bytes(stored[0:4], "little")
    sv = (ec >> 13) & 31
    _crypt(stored, 8, PK7_STORED, ec)
    stored[8:PK7_STORED] = _unshuffle(bytes(stored[8:PK7_STORED]), sv)
    return bytes(stored)


def encrypt_pk7(plain: bytes) -> bytes:
    if len(plain) < PK7_STORED:
        raise Pk7Error(f"PK7 blob is {len(plain)} bytes; need {PK7_STORED}")
    stored = bytearray(plain[:PK7_STORED])
    ec = int.from_bytes(stored[0:4], "little")
    sv = (ec >> 13) & 31
    stored[8:PK7_STORED] = _shuffle(bytes(stored[8:PK7_STORED]), sv)
    _crypt(stored, 8, PK7_STORED, ec)
    return bytes(stored)


def parse_pk7(blob: bytes) -> Pk7:
    decrypted = decrypt_pk7(blob)
    checksum = int.from_bytes(decrypted[6:8], "little")
    calc = pk7_checksum(decrypted)
    species = int.from_bytes(decrypted[0x08:0x0A], "little")
    tid = int.from_bytes(decrypted[0x0C:0x0E], "little")
    sid = int.from_bytes(decrypted[0x0E:0x10], "little")
    pid = int.from_bytes(decrypted[0x18:0x1C], "little")
    ec = int.from_bytes(decrypted[0:4], "little")
    if checksum != calc:
        raise Pk7Error(
            f"PK7 checksum mismatch (stored=0x{checksum:04X} calc=0x{calc:04X})"
        )
    if species == 0 or species > NATIONAL_DEX_MAX:
        raise Pk7Error(f"PK7 species {species} is not a valid National Dex id")
    return Pk7(
        encryption_constant=ec,
        species=species,
        tid=tid,
        sid=sid,
        pid=pid,
        checksum=checksum,
        checksum_ok=True,
    )


def build_pk7(
    *,
    species: int,
    pid: int,
    tid: int,
    sid: int,
    encryption_constant: int,
) -> bytes:
    """Minimal decrypted stored PK7 for tests (checksum filled in)."""
    data = bytearray(PK7_STORED)
    struct.pack_into("<I", data, 0, encryption_constant)
    struct.pack_into("<H", data, 0x08, species)
    struct.pack_into("<H", data, 0x0C, tid)
    struct.pack_into("<H", data, 0x0E, sid)
    struct.pack_into("<I", data, 0x18, pid)
    struct.pack_into("<H", data, 6, pk7_checksum(data))
    return bytes(data)
