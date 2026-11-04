"""Household catalog checks. Run: python -m unittest corpus.test_validate_households"""

from __future__ import annotations

import json
import unittest

from corpus.load_catalog import CATALOG_PATH, validate_catalog
from corpus.validate_households import (
    HOUSEHOLDS_PATH,
    HouseholdError,
    validate_household_file,
    validate_households,
)


def _attributes() -> list[dict]:
    return validate_catalog(json.loads(CATALOG_PATH.read_text()))


def _rows() -> list[dict]:
    return json.loads(HOUSEHOLDS_PATH.read_text())


class HouseholdCatalogTest(unittest.TestCase):
    def test_proof_households_are_accepted(self) -> None:
        rows = validate_household_file()
        self.assertEqual(len(rows), 40)
        self.assertEqual(rows[0]["household_id"], "h01")

    def test_missing_field_rejects_the_file(self) -> None:
        rows = _rows()
        del rows[3]["region"]
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())

    def test_forbidden_field_rejects_the_file(self) -> None:
        rows = _rows()
        rows[0]["age_years"] = 40
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())

    def test_integer_outside_catalog_bounds_rejects_the_file(self) -> None:
        rows = _rows()
        rows[1]["tenure_months"] = 241
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())

    def test_unknown_enum_rejects_the_file(self) -> None:
        rows = _rows()
        rows[2]["region"] = "east"
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())

    def test_boolean_must_be_json_boolean(self) -> None:
        rows = _rows()
        rows[4]["autopay"] = "true"
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())

    def test_duplicate_household_id_rejects_the_file(self) -> None:
        rows = _rows()
        rows[5]["household_id"] = rows[0]["household_id"]
        with self.assertRaises(HouseholdError):
            validate_households(rows, _attributes())


if __name__ == "__main__":
    unittest.main()
