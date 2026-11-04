"""Plan-and-revise checks. Run: python -m unittest tests.test_graph"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from builder.graph import run_graph
from builder.planner import PlannerError, ScriptedPlanner
from builder.schemas import PriorAttempt

AT_RISK = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2},
    ]
}
EMPTY = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 240},
        {"field": "tenure_months", "op": "lte", "value": 0},
    ]
}
BROAD = {"all": [{"field": "tenure_months", "op": "gte", "value": 0}]}
AGE = {"all": [{"field": "age_years", "op": "gte", "value": 18}]}


class RaisingPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, objective: str, usable_names: list[str], prior: PriorAttempt | None) -> dict:
        self.calls += 1
        raise PlannerError("no predicate")


class GraphTest(unittest.TestCase):
    def test_a_count_in_range_returns_a_draft_audience(self) -> None:
        planner = ScriptedPlanner([AT_RISK, AT_RISK])
        audience, written, records = _run(planner, "run-accept")
        self.assertEqual(audience.status, "draft")
        self.assertEqual(audience.estimated_size, 2147)
        self.assertEqual(audience.predicates.model_dump(), AT_RISK)
        self.assertEqual(len(planner.calls), 1)
        self.assertIsNone(planner.calls[0][2])
        self.assertEqual(len(planner.calls[0][1]), 11)
        self.assertNotIn("age_years", planner.calls[0][1])
        self.assertEqual(written, ["tool.jsonl"])
        self.assertEqual([record["tool"] for record in records], ["list_usable_attributes", "count_audience"])
        self.assertEqual({record["run_id"] for record in records}, {"run-accept"})

    def test_an_empty_count_is_revised(self) -> None:
        planner = ScriptedPlanner([EMPTY, AT_RISK])
        audience, _, _ = _run(planner, "run-empty")
        prior = planner.calls[1][2]
        self.assertEqual(audience.estimated_size, 2147)
        self.assertEqual(prior.count, 0)
        self.assertIsNone(prior.error_class)

    def test_a_broad_count_is_revised(self) -> None:
        planner = ScriptedPlanner([BROAD, AT_RISK])
        audience, _, _ = _run(planner, "run-broad")
        prior = planner.calls[1][2]
        self.assertEqual(audience.estimated_size, 2147)
        self.assertGreater(prior.count, 2500)

    def test_a_forbidden_field_is_revised_then_stopped(self) -> None:
        revised = ScriptedPlanner([AGE, AT_RISK])
        audience, _, records = _run(revised, "run-forbid")
        self.assertEqual(audience.estimated_size, 2147)
        self.assertEqual(revised.calls[1][2].error_class, "forbidden_field")
        self.assertEqual(records[1]["error_class"], "forbidden_field")

        stopped = ScriptedPlanner([AGE, AGE, AGE])
        audience, written, records = _run(stopped, "run-g07", "Households targeted by age.")
        self.assertIsNone(audience)
        self.assertEqual(len(stopped.calls), 3)
        self.assertEqual(written, ["tool.jsonl"])
        rejections = [record for record in records if record["tool"] == "count_audience"]
        self.assertEqual(len(rejections), 3)
        self.assertTrue(all(record["error_class"] == "forbidden_field" for record in rejections))
        self.assertEqual({record["run_id"] for record in records}, {"run-g07"})

    def test_a_planner_that_raises_returns_nothing(self) -> None:
        planner = RaisingPlanner()
        audience, written, records = _run(planner, "run-raise")
        self.assertIsNone(audience)
        self.assertEqual(planner.calls, 3)
        self.assertEqual(written, ["tool.jsonl"])
        self.assertEqual([record["tool"] for record in records], ["list_usable_attributes"])


def _run(planner: object, run_id: str, objective: str = "Month-to-month households with recent support contact."):
    with tempfile.TemporaryDirectory() as directory:
        log_path = Path(directory) / "tool.jsonl"
        audience = run_graph(objective, planner, log_path=log_path, run_id=run_id)
        written = sorted(path.name for path in Path(directory).iterdir())
        records = [json.loads(line) for line in log_path.read_text().splitlines()]
    return audience, written, records


if __name__ == "__main__":
    unittest.main()
