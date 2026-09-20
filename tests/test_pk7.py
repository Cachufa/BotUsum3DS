"""PK7 decrypt / SV (no Azahar, no save file)."""

from __future__ import annotations

import unittest

from botusum.pk7 import (
    SHINY_SV_LIMIT,
    Pk7Error,
    build_pk7,
    decrypt_pk7,
    encrypt_pk7,
    is_shiny,
    parse_pk7,
    shiny_value,
)


class ShinyValueTests(unittest.TestCase):
    def test_non_shiny_example(self) -> None:
        # pid=0x12345678 tid=0x1111 sid=0x2222
        sv = shiny_value(0x12345678, 0x1111, 0x2222)
        self.assertEqual(sv, (0x1234 ^ 0x5678 ^ 0x1111 ^ 0x2222) & 0xFFFF)
        self.assertFalse(is_shiny(sv))

    def test_shiny_threshold(self) -> None:
        self.assertEqual(shiny_value(0x00010000, 1, 0), 0)
        self.assertTrue(is_shiny(0))
        self.assertTrue(is_shiny(15))
        self.assertFalse(is_shiny(16))
        self.assertEqual(SHINY_SV_LIMIT, 16)
        self.assertEqual(shiny_value(0x00010010, 1, 0), 16)
        self.assertFalse(is_shiny(shiny_value(0x00010010, 1, 0)))


class Pk7RoundtripTests(unittest.TestCase):
    def test_encrypt_decrypt_poipole(self) -> None:
        plain = build_pk7(
            species=803,
            pid=0xA1B2C3D4,
            tid=12345,
            sid=54321,
            encryption_constant=0x13579BDF,
        )
        encrypted = encrypt_pk7(plain)
        self.assertNotEqual(encrypted[8:232], plain[8:232])
        self.assertEqual(decrypt_pk7(encrypted), plain)
        parsed = parse_pk7(encrypted)
        self.assertEqual(parsed.species, 803)
        self.assertEqual(parsed.pid, 0xA1B2C3D4)
        self.assertEqual(parsed.tid, 12345)
        self.assertEqual(parsed.sid, 54321)
        self.assertTrue(parsed.checksum_ok)
        self.assertEqual(parsed.sv, shiny_value(0xA1B2C3D4, 12345, 54321))
        self.assertFalse(parsed.shiny)

    def test_shiny_poipole(self) -> None:
        plain = build_pk7(
            species=803,
            pid=0x00010000,
            tid=1,
            sid=0,
            encryption_constant=0x11111111,
        )
        parsed = parse_pk7(encrypt_pk7(plain))
        self.assertEqual(parsed.sv, 0)
        self.assertTrue(parsed.shiny)

    def test_empty_slot_rejected(self) -> None:
        with self.assertRaises(Pk7Error):
            parse_pk7(b"\x00" * 232)

    def test_corrupt_checksum_rejected(self) -> None:
        plain = bytearray(
            build_pk7(
                species=803,
                pid=1,
                tid=2,
                sid=3,
                encryption_constant=0x22222222,
            )
        )
        plain[0x08] ^= 0xFF
        with self.assertRaises(Pk7Error):
            parse_pk7(encrypt_pk7(bytes(plain)))


if __name__ == "__main__":
    unittest.main()
