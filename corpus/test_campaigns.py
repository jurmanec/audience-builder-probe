"""Campaign library shape. Run: python -m unittest corpus.test_campaigns"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS_PATH = ROOT / "corpus" / "campaigns.json"
GOLD_PATH = ROOT / "eval" / "gold.json"
REQUIRED = {"id", "name", "offer", "channels", "constraint", "outcome"}


class CampaignLibraryTest(unittest.TestCase):
    def test_library_has_four_campaigns_and_does_not_copy_gold_objectives(self) -> None:
        campaigns = json.loads(CAMPAIGNS_PATH.read_text())
        objectives = json.loads(GOLD_PATH.read_text())
        self.assertEqual([item["id"] for item in campaigns], [f"c0{n}" for n in range(1, 5)])
        library_text = json.dumps(campaigns)
        for campaign in campaigns:
            self.assertEqual(set(campaign), REQUIRED)
            self.assertTrue(campaign["name"])
            self.assertTrue(campaign["offer"])
            self.assertTrue(campaign["channels"])
            self.assertTrue(campaign["constraint"])
            self.assertTrue(campaign["outcome"])
        for objective in objectives:
            self.assertNotIn(objective["objective"], library_text)


if __name__ == "__main__":
    unittest.main()
