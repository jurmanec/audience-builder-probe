"""One-shot checks. Run: python -m unittest tests.test_oneshot"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from builder.oneshot import run_oneshot
from builder.oneshot_runner import main, write_audience
from builder.planner import MODEL_ID, PlannerError, ScriptedPlanner, XAIOneShot, plan_predicate
from builder.schemas import Predicate

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
NAMES = ["tenure_months", "contract_status", "support_contacts_90d"]


class OneShotTest(unittest.TestCase):
    def test_a_count_in_range_returns_a_draft_audience(self) -> None:
        planner = ScriptedPlanner([AT_RISK, AT_RISK])
        audience, records = _run(planner, "run-accept")
        self.assertEqual(audience.status, "draft")
        self.assertEqual(audience.estimated_size, 2147)
        self.assertEqual(audience.predicates.model_dump(), AT_RISK)
        self.assertEqual(len(planner.calls), 1)
        self.assertIsNone(planner.calls[0][2])
        self.assertEqual(len(planner.calls[0][1]), 11)
        self.assertNotIn("age_years", planner.calls[0][1])
        self.assertEqual([record["tool"] for record in records], ["list_usable_attributes", "count_audience"])
        self.assertEqual({record["run_id"] for record in records}, {"run-accept"})

    def test_an_empty_count_returns_nothing(self) -> None:
        planner = ScriptedPlanner([EMPTY, AT_RISK])
        audience, records = _run(planner, "run-empty")
        self.assertIsNone(audience)
        self.assertEqual(len(planner.calls), 1)
        self.assertEqual(records[1]["count"], 0)

    def test_a_broad_count_returns_nothing(self) -> None:
        planner = ScriptedPlanner([BROAD, AT_RISK])
        audience, records = _run(planner, "run-broad")
        self.assertIsNone(audience)
        self.assertEqual(len(planner.calls), 1)
        self.assertGreater(records[1]["count"], 2500)

    def test_a_forbidden_field_returns_nothing(self) -> None:
        planner = ScriptedPlanner([AGE, AT_RISK])
        audience, records = _run(planner, "run-forbid", "Households targeted by age.")
        self.assertIsNone(audience)
        self.assertEqual(len(planner.calls), 1)
        self.assertEqual(records[1]["error_class"], "forbidden_field")

    def test_a_planner_error_returns_nothing_without_a_count(self) -> None:
        planner = RaisingPlanner()
        audience, records = _run(planner, "run-error")
        self.assertIsNone(audience)
        self.assertEqual(planner.calls, 1)
        self.assertEqual([record["tool"] for record in records], ["list_usable_attributes"])

    def test_the_request_has_no_prior_attempt(self) -> None:
        seen: dict[str, dict] = {}

        def transport(payload: dict) -> str:
            seen["payload"] = payload
            return json.dumps({"choices": [{"message": {"content": json.dumps(AT_RISK)}}]})

        planner = XAIOneShot(api_key="test-key", transport=transport)
        predicate = plan_predicate("at-risk renewal households", NAMES, planner=planner)
        payload = seen["payload"]
        user = json.loads(payload["messages"][1]["content"])
        self.assertEqual(payload["model"], MODEL_ID)
        self.assertNotIn("prior_attempt", user)
        self.assertNotIn("test-key", json.dumps(payload))
        contract = next(item for item in user["attributes"] if item["name"] == "contract_status")
        self.assertEqual(contract["values"], ["month_to_month", "in_term"])
        self.assertEqual(predicate, Predicate.model_validate(AT_RISK))

    def test_a_missing_api_key_makes_no_live_call(self) -> None:
        calls: list[dict] = []

        def transport(payload: dict) -> str:
            calls.append(payload)
            return ""

        planner = XAIOneShot(api_key="", transport=transport)
        with self.assertRaises(PlannerError):
            plan_predicate("at-risk renewal households", NAMES, planner=planner)
        self.assertEqual(calls, [])

    def test_a_completed_call_writes_only_the_audience_file(self) -> None:
        planner = ScriptedPlanner([AT_RISK])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audience.json"
            wrote = write_audience(
                "Month-to-month households with at least a year of tenure and recent support contact.",
                destination,
                planner,
                log_path=Path(directory) / "tool.jsonl",
                run_id="run-write",
            )
            self.assertTrue(wrote)
            audience = json.loads(destination.read_text())
            self.assertEqual(audience["status"], "draft")
            self.assertEqual(audience["estimated_size"], 2147)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()), ["audience.json", "tool.jsonl"])

    def test_a_miss_leaves_an_existing_file_in_place(self) -> None:
        planner = ScriptedPlanner([AGE])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audience.json"
            destination.write_text("keep\n")
            wrote = write_audience(
                "Households targeted by age.",
                destination,
                planner,
                log_path=Path(directory) / "tool.jsonl",
                run_id="run-miss",
            )
            self.assertFalse(wrote)
            self.assertEqual(destination.read_text(), "keep\n")

    def test_command_writes_nothing_when_the_api_key_is_missing(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": ""}), tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audience.json"
            code = main(
                [
                    "Month-to-month households with at least a year of tenure and recent support contact.",
                    "--out",
                    str(destination),
                ]
            )
            self.assertEqual(code, 2)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])


class RaisingPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, objective: str, usable_names: list[str], prior: object) -> dict:
        self.calls += 1
        raise PlannerError("no predicate")


def _run(planner: object, run_id: str, objective: str = "at-risk renewal households") -> tuple:
    with tempfile.TemporaryDirectory() as directory:
        log_path = Path(directory) / "tool.jsonl"
        audience = run_oneshot(objective, planner, log_path=log_path, run_id=run_id)
        records = [json.loads(line) for line in log_path.read_text().splitlines()]
    return audience, records


if __name__ == "__main__":
    unittest.main()
