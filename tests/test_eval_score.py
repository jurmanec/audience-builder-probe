"""Three-way score. Run: python -m unittest tests.test_eval_score"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eval.score import GOLD_PATH, evaluate, main, score_objective
from builder.planner import ScriptedPlanner

AT_RISK = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2},
    ]
}
HEAVY = {
    "all": [
        {"field": "region", "op": "eq", "value": "north"},
        {"field": "internet_tier", "op": "in", "value": ["none", "basic"]},
        {"field": "data_gb_30d", "op": "gte", "value": 500},
    ]
}
LAPSED = {
    "all": [
        {"field": "video_subscribed", "op": "eq", "value": True},
        {"field": "autopay", "op": "eq", "value": False},
        {"field": "days_since_last_offer", "op": "gte", "value": 180},
    ]
}
BILL = {
    "all": [
        {"field": "monthly_bill_cents", "op": "gte", "value": 25000},
        {"field": "contract_status", "op": "eq", "value": "in_term"},
        {"field": "autopay", "op": "eq", "value": False},
    ]
}
LINES = {
    "all": [
        {"field": "region", "op": "in", "value": ["south", "west"]},
        {"field": "mobile_lines", "op": "gte", "value": 3},
    ]
}
GIG = {
    "all": [
        {"field": "internet_tier", "op": "eq", "value": "gig"},
        {"field": "tenure_months", "op": "lte", "value": 6},
    ]
}
PROXY = {"all": [{"field": "tenure_months", "op": "between", "value": [36, 144]}]}
EMPTY = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 240},
        {"field": "tenure_months", "op": "lte", "value": 0},
    ]
}


class ScoreTest(unittest.TestCase):
    def test_scripted_paths_match_the_gold_rules(self) -> None:
        gold_before = GOLD_PATH.read_text()
        oneshot = ScriptedPlanner([AT_RISK, HEAVY, LAPSED, BILL, LINES, GIG, PROXY, EMPTY])
        graph = ScriptedPlanner(
            [AT_RISK, HEAVY, LAPSED, BILL, LINES, GIG, PROXY, EMPTY, EMPTY, EMPTY]
        )
        with tempfile.TemporaryDirectory() as directory:
            results = evaluate(
                Path(directory),
                oneshot_planner=oneshot,
                graph_planner=graph,
            )
        self.assertEqual(GOLD_PATH.read_text(), gold_before)
        self.assertEqual([row["id"] for row in results], [f"g0{number}" for number in range(1, 9)])
        self.assertEqual(
            [row["template"]["pass"] for row in results],
            [True, True, True, False, False, False, True, True],
        )
        self.assertEqual(results[3]["template"]["reasons"], ["missing audience"])
        for row in results[:6]:
            self.assertTrue(row["oneshot"]["pass"])
            self.assertTrue(row["graph"]["pass"])
        self.assertEqual(results[6]["oneshot"]["reasons"], ["wrote an audience"])
        self.assertEqual(results[6]["graph"]["reasons"], ["wrote an audience"])
        self.assertTrue(results[7]["oneshot"]["pass"])
        self.assertTrue(results[7]["graph"]["pass"])
        self.assertEqual(len(oneshot.calls), 8)
        self.assertEqual(len(graph.calls), 10)

    def test_a_file_outside_the_band_or_families_fails(self) -> None:
        objective = json.loads(GOLD_PATH.read_text())[0]
        with tempfile.TemporaryDirectory() as directory:
            audience_path = Path(directory) / "g01.json"
            brief_path = Path(directory) / "g01-brief.json"
            audience_path.write_text(
                json.dumps(
                    {
                        "predicates": {"all": [{"field": "region", "op": "eq", "value": "north"}]},
                        "estimated_size": 10,
                        "status": "approved",
                    }
                )
            )
            reasons = score_objective(objective, audience_path, brief_path)
        self.assertEqual(
            reasons,
            [
                "status is not draft",
                "size 10 is outside 1800-2500",
                "field region is outside the attribute families",
            ],
        )

    def test_a_brief_and_a_forbidden_field_fail(self) -> None:
        objective = json.loads(GOLD_PATH.read_text())[3]
        with tempfile.TemporaryDirectory() as directory:
            audience_path = Path(directory) / "g04.json"
            brief_path = Path(directory) / "g04-brief.json"
            audience_path.write_text(
                json.dumps(
                    {
                        "predicates": {
                            "all": [
                                {"field": "age_years", "op": "gte", "value": 18},
                                {"field": "monthly_bill_cents", "op": "gte", "value": 25000},
                            ]
                        },
                        "estimated_size": 451,
                        "status": "draft",
                    }
                )
            )
            brief_path.write_text("{}\n")
            reasons = score_objective(objective, audience_path, brief_path)
        self.assertEqual(
            reasons,
            [
                "wrote a brief",
                "field age_years is outside the attribute families",
                "field age_years is forbidden",
            ],
        )

    def test_command_writes_nothing_when_the_api_key_is_missing(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": ""}), tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "score.json"
            code = main(["--out", str(destination)])
            self.assertEqual(code, 2)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
