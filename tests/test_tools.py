"""Typed tool checks. Run: python -m unittest tests.test_tools"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from builder.tools import count_audience, list_campaigns, list_usable_attributes

AT_RISK = {
    "predicate": {
        "all": [
            {"field": "tenure_months", "op": "gte", "value": 12},
            {"field": "contract_status", "op": "eq", "value": "month_to_month"},
            {"field": "support_contacts_90d", "op": "gte", "value": 2},
        ]
    }
}


class ToolTest(unittest.TestCase):
    def test_at_risk_predicate_returns_the_population_count(self) -> None:
        result = count_audience(AT_RISK)
        self.assertEqual(result.count, 2147)
        self.assertIsNone(result.error_class)

    def test_forbidden_field_is_a_rejection_in_the_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            log_path = directory_path / "tool.jsonl"
            result = count_audience(
                {"predicate": {"all": [{"field": "age_years", "op": "gte", "value": 18}]}},
                log_path=log_path,
                run_id="run-1",
            )
            record = json.loads(log_path.read_text().strip())
            written = sorted(path.name for path in directory_path.iterdir())
        self.assertIsNone(result.count)
        self.assertEqual(result.error_class, "forbidden_field")
        self.assertEqual(record["tool"], "count_audience")
        self.assertEqual(record["run_id"], "run-1")
        self.assertEqual(record["outcome"], "rejection")
        self.assertEqual(record["error_class"], "forbidden_field")
        self.assertGreaterEqual(record["duration_ms"], 0)
        self.assertEqual(written, ["tool.jsonl"])

    def test_list_campaigns_returns_the_library_and_logs_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            log_path = directory_path / "tool.jsonl"
            result = list_campaigns(log_path=log_path, run_id="run-campaigns")
            record = json.loads(log_path.read_text().strip())
            written = sorted(path.name for path in directory_path.iterdir())
        self.assertEqual([campaign.id for campaign in result.campaigns], ["c01", "c02", "c03", "c04"])
        self.assertEqual(result.campaigns[0].offer, "A bill credit for switching to paperless billing.")
        self.assertEqual(result.campaigns[1].channels, ["email", "sms"])
        self.assertEqual(record["tool"], "list_campaigns")
        self.assertEqual(record["run_id"], "run-campaigns")
        self.assertEqual(record["arguments"], {})
        self.assertEqual(record["outcome"], "pass")
        self.assertGreaterEqual(record["duration_ms"], 0)
        self.assertNotIn("count", record)
        self.assertNotIn("error_class", record)
        self.assertEqual(written, ["tool.jsonl"])

    def test_list_usable_attributes_omits_forbidden_fields(self) -> None:
        names = list_usable_attributes().names
        self.assertEqual(len(names), 11)
        self.assertIn("tenure_months", names)
        self.assertNotIn("age_years", names)
        self.assertNotIn("household_income_cents", names)
        self.assertNotIn("ethnicity", names)


if __name__ == "__main__":
    unittest.main()
