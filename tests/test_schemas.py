"""Shared schema checks. Run: python -m unittest tests.test_schemas"""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from builder.schemas import Audience, Brief, CatalogResult, CountResult, Predicate


def _audience(**overrides: object) -> Audience:
    payload = {
        "predicates": {
            "all": [
                {"field": "tenure_months", "op": "gte", "value": 12},
            ]
        },
        "estimated_size": 2147,
        "status": "draft",
    }
    payload.update(overrides)
    return Audience.model_validate(payload)


class SchemaTest(unittest.TestCase):
    def test_audience_accepts_a_draft_record(self) -> None:
        audience = _audience()
        self.assertEqual(audience.estimated_size, 2147)
        self.assertEqual(audience.status, "draft")

    def test_audience_rejects_a_negative_size(self) -> None:
        with self.assertRaises(ValidationError):
            _audience(estimated_size=-1)

    def test_predicate_rejects_an_empty_all_list(self) -> None:
        with self.assertRaises(ValidationError):
            Predicate.model_validate({"all": []})

    def test_brief_requires_an_approved_audience_and_every_field(self) -> None:
        audience = _audience(status="approved")
        brief = Brief.model_validate(
            {
                "audience": audience.model_dump(),
                "campaign_id": "c01",
                "offer": "A bill credit for switching to paperless billing.",
                "channels": ["email"],
                "constraint": "Do not mention contract status.",
            }
        )
        self.assertEqual(brief.campaign_id, "c01")
        with self.assertRaises(ValidationError):
            Brief.model_validate(
                {
                    "audience": _audience().model_dump(),
                    "campaign_id": "c01",
                    "offer": "A bill credit.",
                    "channels": ["email"],
                    "constraint": "Do not mention contract status.",
                }
            )

    def test_count_result_is_a_count_or_a_rejection(self) -> None:
        self.assertEqual(CountResult(count=2147).count, 2147)
        self.assertEqual(CountResult(error_class="forbidden_field").error_class, "forbidden_field")
        with self.assertRaises(ValidationError):
            CountResult(count=2147, error_class="forbidden_field")
        with self.assertRaises(ValidationError):
            CountResult()

    def test_catalog_result_lists_unique_names(self) -> None:
        names = CatalogResult(names=["tenure_months", "region"]).names
        self.assertEqual(names, ["tenure_months", "region"])
        with self.assertRaises(ValidationError):
            CatalogResult(names=["region", "region"])


if __name__ == "__main__":
    unittest.main()
