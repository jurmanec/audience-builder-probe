"""Household load checks. Run: python -m unittest corpus.test_load_households"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from corpus.load_catalog import CATALOG_PATH, load_catalog
from corpus.load_households import load_households
from corpus.validate_households import HOUSEHOLDS_PATH, HouseholdError


class HouseholdLoadTest(unittest.TestCase):
    def test_proof_households_load_and_catalog_reload_keeps_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "intake.duckdb"
            count = load_households(HOUSEHOLDS_PATH, CATALOG_PATH, db_path)
            self.assertEqual(count, 40)

            import duckdb

            connection = duckdb.connect(str(db_path))
            try:
                columns = connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'household'
                    ORDER BY ordinal_position
                    """
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(columns[0][0], "household_id")
            self.assertIn("tenure_months", [name for (name,) in columns])
            self.assertNotIn("age_years", [name for (name,) in columns])

            load_catalog(CATALOG_PATH, db_path)
            connection = duckdb.connect(str(db_path))
            try:
                kept = connection.execute("SELECT count(*) FROM household").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(kept, 40)

    def test_rejected_file_does_not_replace_the_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            db_path = directory_path / "intake.duckdb"
            load_households(HOUSEHOLDS_PATH, CATALOG_PATH, db_path)

            broken_path = directory_path / "broken.json"
            rows = json.loads(HOUSEHOLDS_PATH.read_text())
            rows[0]["age_years"] = 40
            broken_path.write_text(json.dumps(rows))

            with self.assertRaises(HouseholdError):
                load_households(broken_path, CATALOG_PATH, db_path)

            import duckdb

            connection = duckdb.connect(str(db_path))
            try:
                count = connection.execute("SELECT count(*) FROM household").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, 40)


if __name__ == "__main__":
    unittest.main()
