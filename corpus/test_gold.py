"""Gold-set shape. Run: python -m unittest corpus.test_gold"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

GOLD_PATH = Path(__file__).resolve().parents[1] / "eval" / "gold.json"
SHARED = {
    "id",
    "objective",
    "attribute_families",
    "forbidden_fields",
    "template_intent",
}
FORBIDDEN = {"age_years", "household_income_cents", "ethnicity"}


class GoldSetTest(unittest.TestCase):
    def test_gold_file_has_scored_and_fail_closed_objectives(self) -> None:
        objectives = json.loads(GOLD_PATH.read_text())
        self.assertEqual([item["id"] for item in objectives], [f"g0{n}" for n in range(1, 9)])
        templates = []
        for item in objectives[:6]:
            self.assertEqual(set(item), SHARED | {"size_band"})
            self._assert_common(item)
            band = item["size_band"]
            self.assertLess(band["min"], band["max"])
            templates.append(item["template_intent"])
        for item in objectives[6:]:
            self.assertEqual(set(item), SHARED | {"outcome"})
            self._assert_common(item)
            self.assertEqual(item["outcome"], "no_audience")
            self.assertNotIn("size_band", item)
            templates.append(item["template_intent"])
        self.assertEqual(
            templates,
            [
                "at-risk renewal",
                "heavy-use upgrade",
                "lapsed video offer",
                None,
                None,
                None,
                None,
                None,
            ],
        )

    def _assert_common(self, item: dict) -> None:
        self.assertNotIn("predicate", item)
        self.assertNotIn("count", item)
        self.assertTrue(item["objective"])
        self.assertTrue(item["attribute_families"])
        self.assertTrue(FORBIDDEN <= set(item["forbidden_fields"]))


if __name__ == "__main__":
    unittest.main()
