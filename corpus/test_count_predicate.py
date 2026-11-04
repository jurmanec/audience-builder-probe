"""Predicate counts. Run: python -m unittest corpus.test_count_predicate"""

from __future__ import annotations

import json
import unittest

from corpus.count_predicate import PredicateError, count_predicate
from corpus.generate_households import POPULATION_PATH
from corpus.load_catalog import CATALOG_PATH, validate_catalog

GOLD_PATH = POPULATION_PATH.parents[1] / "eval" / "gold.json"

AT_RISK = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2},
    ]
}
HEAVY_USE = {
    "all": [
        {"field": "region", "op": "eq", "value": "north"},
        {"field": "internet_tier", "op": "in", "value": ["none", "basic"]},
        {"field": "data_gb_30d", "op": "gte", "value": 500},
    ]
}
LAPSED_VIDEO = {
    "all": [
        {"field": "video_subscribed", "op": "eq", "value": True},
        {"field": "autopay", "op": "eq", "value": False},
        {"field": "days_since_last_offer", "op": "gte", "value": 180},
    ]
}


def _attributes() -> list[dict]:
    return validate_catalog(json.loads(CATALOG_PATH.read_text()))


def _rows() -> list[dict]:
    return json.loads(POPULATION_PATH.read_text())


def _band(objective_id: str) -> dict:
    objectives = json.loads(GOLD_PATH.read_text())
    return next(item["size_band"] for item in objectives if item["id"] == objective_id)


class CountPredicateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.attributes = _attributes()
        cls.rows = _rows()

    def test_template_counts_fall_inside_gold_bands(self) -> None:
        cases = (
            (AT_RISK, 2147, "g01"),
            (HEAVY_USE, 440, "g02"),
            (LAPSED_VIDEO, 1052, "g03"),
        )
        for predicate, expected, objective_id in cases:
            count = count_predicate(predicate, self.rows, self.attributes)
            band = _band(objective_id)
            self.assertEqual(count, expected)
            self.assertGreaterEqual(count, band["min"])
            self.assertLessEqual(count, band["max"])

    def test_forbidden_field_is_rejected(self) -> None:
        predicate = {"all": [{"field": "age_years", "op": "gte", "value": 18}]}
        with self.assertRaises(PredicateError):
            count_predicate(predicate, self.rows, self.attributes)

    def test_integer_comparison_outside_catalog_bounds_is_rejected(self) -> None:
        predicate = {"all": [{"field": "tenure_months", "op": "gte", "value": 241}]}
        with self.assertRaises(PredicateError):
            count_predicate(predicate, [{"tenure_months": 12}], self.attributes)

    def test_between_is_inclusive(self) -> None:
        predicate = {"all": [{"field": "tenure_months", "op": "between", "value": [12, 12]}]}
        rows = [{"tenure_months": 11}, {"tenure_months": 12}, {"tenure_months": 13}]
        self.assertEqual(count_predicate(predicate, rows, self.attributes), 1)

    def test_boolean_rejects_a_non_eq_operator(self) -> None:
        predicate = {"all": [{"field": "autopay", "op": "gte", "value": True}]}
        with self.assertRaises(PredicateError):
            count_predicate(predicate, [{"autopay": True}], self.attributes)


if __name__ == "__main__":
    unittest.main()
