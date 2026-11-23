"""Hunt list resolution (no Azahar, no TTY arrows)."""

from __future__ import annotations

import io
import unittest

from botusum.picker import (
    HUNTS,
    PickerError,
    resolve_choice,
    select_hunt,
)


class ResolveChoiceTests(unittest.TestCase):
    def test_poipole_by_id_and_number(self) -> None:
        by_id = resolve_choice("poipole")
        by_num = resolve_choice("1")
        self.assertIs(by_id, HUNTS[0])
        self.assertIs(by_num, HUNTS[0])
        self.assertTrue(by_id.implemented)
        self.assertEqual(by_id.species, 803)

    def test_type_null_by_id_and_number(self) -> None:
        hunt = resolve_choice("type-null")
        self.assertTrue(hunt.implemented)
        self.assertEqual(hunt.sequence, "type-null")
        self.assertEqual(hunt.species, 772)
        self.assertEqual(hunt, resolve_choice("2"))

    def test_unknown_and_empty(self) -> None:
        with self.assertRaises(PickerError):
            resolve_choice("tapu-koko")
        with self.assertRaises(PickerError):
            resolve_choice("0")
        with self.assertRaises(PickerError):
            resolve_choice("  ")


class SelectHuntTests(unittest.TestCase):
    def test_flag_skips_list(self) -> None:
        hunt = select_hunt("poipole", stdin=io.StringIO(), stdout=io.StringIO())
        self.assertEqual(hunt.id, "poipole")

    def test_piped_number(self) -> None:
        stdout = io.StringIO()
        hunt = select_hunt(None, stdin=io.StringIO("2\n"), stdout=stdout)
        self.assertEqual(hunt.id, "type-null")
        self.assertIn("[1] Poipole", stdout.getvalue())
        self.assertIn("[2] Type: Null", stdout.getvalue())

    def test_empty_pipe_asks_for_flag(self) -> None:
        with self.assertRaises(PickerError) as ctx:
            select_hunt(None, stdin=io.StringIO(""), stdout=io.StringIO())
        self.assertIn("--hunt poipole", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
