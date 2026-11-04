"""Grounded brief checks. Run: python -m unittest tests.test_brief"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from builder.brief import ScriptedCampaignChooser, XAICampaignChooser, draft_brief

AUDIENCE = {
    "predicates": {
        "all": [
            {"field": "tenure_months", "op": "gte", "value": 12},
        ]
    },
    "estimated_size": 2147,
    "status": "approved",
}


class BriefTest(unittest.TestCase):
    def test_an_approved_audience_copies_the_chosen_campaign(self) -> None:
        chooser = ScriptedCampaignChooser("c01")
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            log_path = directory_path / "tool.jsonl"
            brief = draft_brief(AUDIENCE, chooser, log_path=log_path, run_id="run-brief")
            record = json.loads(log_path.read_text().strip())
            written = sorted(path.name for path in directory_path.iterdir())
        self.assertEqual(brief.campaign_id, "c01")
        self.assertEqual(brief.offer, "A bill credit for switching to paperless billing.")
        self.assertEqual(brief.channels, ["email"])
        self.assertEqual(brief.constraint, "Do not mention contract status.")
        self.assertEqual(brief.audience.status, "approved")
        self.assertEqual(brief.audience.estimated_size, 2147)
        self.assertEqual([campaign.id for campaign in chooser.calls[0][1]], ["c01", "c02", "c03", "c04"])
        self.assertEqual(record["tool"], "list_campaigns")
        self.assertEqual(record["run_id"], "run-brief")
        self.assertEqual(record["outcome"], "pass")
        self.assertEqual(written, ["tool.jsonl"])

    def test_a_draft_audience_stops_before_the_chooser(self) -> None:
        chooser = ScriptedCampaignChooser("c01")
        draft = {**AUDIENCE, "status": "draft"}
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "tool.jsonl"
            brief = draft_brief(draft, chooser, log_path=log_path, run_id="run-draft")
            written = list(Path(directory).iterdir())
        self.assertIsNone(brief)
        self.assertEqual(chooser.calls, [])
        self.assertEqual(written, [])

    def test_an_unknown_campaign_returns_nothing(self) -> None:
        chooser = ScriptedCampaignChooser("c99")
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "tool.jsonl"
            brief = draft_brief(AUDIENCE, chooser, log_path=log_path, run_id="run-missing")
        self.assertIsNone(brief)
        self.assertEqual(len(chooser.calls), 1)

    def test_the_default_chooser_makes_no_live_call(self) -> None:
        chooser = XAICampaignChooser()
        self.assertIsNone(chooser.model_id)
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "tool.jsonl"
            brief = draft_brief(AUDIENCE, log_path=log_path, run_id="run-xai")
        self.assertIsNone(brief)


if __name__ == "__main__":
    unittest.main()
