"""Population generator checks. Run: python -m unittest corpus.test_generate_households"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from corpus.generate_households import (
    POPULATION_PATH,
    ROW_COUNT,
    SEED,
    generate_rows,
    write_population,
)
from corpus.load_catalog import CATALOG_PATH, validate_catalog
from corpus.load_households import load_households
from corpus.validate_households import validate_households


def _attributes() -> list[dict]:
    return validate_catalog(json.loads(CATALOG_PATH.read_text()))


class GenerateHouseholdsTest(unittest.TestCase):
    def test_same_seed_rebuilds_the_same_rows(self) -> None:
        attributes = _attributes()
        self.assertEqual(
            generate_rows(attributes, ROW_COUNT, SEED),
            generate_rows(attributes, ROW_COUNT, SEED),
        )

    def test_population_file_matches_the_seed_and_loads(self) -> None:
        attributes = _attributes()
        rows = json.loads(POPULATION_PATH.read_text())
        self.assertEqual(rows, generate_rows(attributes, ROW_COUNT, SEED))
        self.assertEqual(len(validate_households(rows, attributes)), ROW_COUNT)
        self.assertEqual(rows[0]["household_id"], "h00001")
        self.assertEqual(rows[-1]["household_id"], "h05000")

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "intake.duckdb"
            self.assertEqual(load_households(POPULATION_PATH, CATALOG_PATH, db_path), ROW_COUNT)

    def test_write_population_rejects_nothing_in_the_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "households.json"
            rows = write_population(path, count=20, seed=SEED)
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["household_id"], "h00001")


if __name__ == "__main__":
    unittest.main()
