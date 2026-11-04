"""At-risk proof query. Run: python -m unittest corpus.test_count_at_risk"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from corpus.count_at_risk import AtRiskMismatch, compare_at_risk
from corpus.load_catalog import CATALOG_PATH
from corpus.load_households import load_households
from corpus.validate_households import HOUSEHOLDS_PATH


class AtRiskProofTest(unittest.TestCase):
    def test_query_matches_ids_recorded_before_sql(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "intake.duckdb"
            load_households(HOUSEHOLDS_PATH, CATALOG_PATH, db_path)
            found = compare_at_risk(db_path)
        self.assertEqual(
            found,
            ["h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08"],
        )

    def test_query_rejects_a_different_expected_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            db_path = directory_path / "intake.duckdb"
            load_households(HOUSEHOLDS_PATH, CATALOG_PATH, db_path)
            expected_path = directory_path / "expected.json"
            expected_path.write_text(
                '{"count": 1, "household_ids": ["h01"]}'
            )
            with self.assertRaises(AtRiskMismatch):
                compare_at_risk(db_path, expected_path)


if __name__ == "__main__":
    unittest.main()
