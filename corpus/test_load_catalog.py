"""Catalog contract checks. Run: python -m unittest corpus.test_load_catalog"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from corpus.load_catalog import CATALOG_PATH, CatalogError, load_catalog, validate_catalog


def _catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text())


class CatalogContractTest(unittest.TestCase):
    def test_starter_catalog_loads_eleven_usable_and_three_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "intake.duckdb"
            counts = load_catalog(CATALOG_PATH, db_path)
        self.assertEqual(counts, [(True, 11), (False, 3)])

    def test_usable_integer_requires_bounds(self) -> None:
        data = _catalog()
        data["attributes"][0].pop("min")
        with self.assertRaises(CatalogError):
            validate_catalog(data)

    def test_usable_enum_requires_values(self) -> None:
        data = _catalog()
        data["attributes"][1]["values"] = []
        with self.assertRaises(CatalogError):
            validate_catalog(data)

    def test_forbidden_attribute_rejects_operators(self) -> None:
        data = _catalog()
        data["attributes"][-1]["operators"] = ["eq"]
        with self.assertRaises(CatalogError):
            validate_catalog(data)


if __name__ == "__main__":
    unittest.main()
