"""Planner interface checks. Run: python -m unittest tests.test_planner"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from builder.planner import MODEL_ID, PlannerError, ScriptedPlanner, XAIPlanner, plan_predicate
from builder.schemas import Predicate, PriorAttempt

AT_RISK = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2},
    ]
}
NAMES = ["tenure_months", "contract_status", "support_contacts_90d"]


class PlannerTest(unittest.TestCase):
    def test_scripted_planner_returns_a_predicate(self) -> None:
        planner = ScriptedPlanner([AT_RISK])
        predicate = plan_predicate("at-risk renewal households", NAMES, planner=planner)
        self.assertEqual(predicate, Predicate.model_validate(AT_RISK))
        self.assertEqual(planner.calls, [("at-risk renewal households", NAMES, None)])

    def test_prior_attempt_is_passed_to_the_planner(self) -> None:
        planner = ScriptedPlanner([AT_RISK])
        prior = {
            "predicate": {"all": [{"field": "age_years", "op": "gte", "value": 18}]},
            "error_class": "forbidden_field",
        }
        plan_predicate("households targeted by age", NAMES, prior, planner)
        attempt = planner.calls[0][2]
        self.assertIsInstance(attempt, PriorAttempt)
        self.assertEqual(attempt.error_class, "forbidden_field")
        self.assertIsNone(attempt.count)

    def test_missing_api_key_makes_no_live_call(self) -> None:
        calls: list[dict] = []

        def transport(payload: dict) -> str:
            calls.append(payload)
            return ""

        planner = XAIPlanner(api_key="", transport=transport)
        self.assertEqual(planner.model_id, MODEL_ID)
        with self.assertRaises(PlannerError):
            plan_predicate("at-risk renewal households", NAMES, planner=planner)
        self.assertEqual(calls, [])

    def test_api_key_is_read_from_the_dotenv_file(self) -> None:
        calls: list[dict] = []

        def transport(payload: dict) -> str:
            calls.append(payload)
            return json.dumps({"choices": [{"message": {"content": json.dumps(AT_RISK)}}]})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('export XAI_API_KEY="from-file"\n')
            planner = XAIPlanner(transport=transport, env_path=path)
            with patch.dict(os.environ):
                os.environ.pop("XAI_API_KEY", None)
                predicate = plan_predicate("at-risk renewal households", NAMES, planner=planner)
        self.assertEqual(predicate, Predicate.model_validate(AT_RISK))
        self.assertEqual(len(calls), 1)
        self.assertNotIn("from-file", json.dumps(calls[0]))

    def test_dotenv_file_does_not_override_an_existing_api_key(self) -> None:
        calls: list[dict] = []

        def transport(payload: dict) -> str:
            calls.append(payload)
            return ""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("XAI_API_KEY=from-file\n")
            planner = XAIPlanner(transport=transport, env_path=path)
            with patch.dict(os.environ, {"XAI_API_KEY": ""}):
                with self.assertRaises(PlannerError):
                    plan_predicate("at-risk renewal households", NAMES, planner=planner)
        self.assertEqual(calls, [])

    def test_xai_request_carries_the_objective_names_and_prior(self) -> None:
        seen: dict[str, dict] = {}

        def transport(payload: dict) -> str:
            seen["payload"] = payload
            return json.dumps({"choices": [{"message": {"content": json.dumps(AT_RISK)}}]})

        prior = {
            "predicate": {"all": [{"field": "age_years", "op": "gte", "value": 18}]},
            "error_class": "forbidden_field",
        }
        planner = XAIPlanner(api_key="test-key", transport=transport)
        predicate = plan_predicate("households targeted by age", NAMES, prior, planner)
        payload = seen["payload"]
        message = json.dumps(payload["messages"])
        self.assertEqual(payload["model"], MODEL_ID)
        self.assertNotIn("test-key", json.dumps(payload))
        self.assertIn("households targeted by age", message)
        self.assertIn("tenure_months", message)
        self.assertIn("forbidden_field", message)
        attributes = json.loads(payload["messages"][1]["content"])["attributes"]
        contract = next(item for item in attributes if item["name"] == "contract_status")
        self.assertEqual(contract["values"], ["month_to_month", "in_term"])
        self.assertNotIn("age_years", [item["name"] for item in attributes])
        self.assertEqual(predicate, Predicate.model_validate(AT_RISK))

    def test_xai_response_that_is_not_a_predicate_is_rejected(self) -> None:
        def transport(payload: dict) -> str:
            return json.dumps({"choices": [{"message": {"content": json.dumps({"all": []})}}]})

        planner = XAIPlanner(api_key="test-key", transport=transport)
        with self.assertRaises(PlannerError):
            plan_predicate("households targeted by age", NAMES, planner=planner)

    def test_empty_objective_and_bad_names_stop_before_the_planner(self) -> None:
        planner = ScriptedPlanner([AT_RISK])
        with self.assertRaises(PlannerError):
            plan_predicate("  ", NAMES, planner=planner)
        with self.assertRaises(PlannerError):
            plan_predicate("at-risk renewal households", [], planner=planner)
        self.assertEqual(planner.calls, [])

    def test_invalid_predicate_and_prior_are_rejected(self) -> None:
        def invalid_predicate(objective: str, usable_names: list[str], prior: PriorAttempt | None) -> dict:
            return {"all": []}

        with self.assertRaises(PlannerError):
            plan_predicate("at-risk renewal households", NAMES, planner=invalid_predicate)
        planner = ScriptedPlanner([AT_RISK])
        with self.assertRaises(PlannerError):
            plan_predicate(
                "at-risk renewal households",
                NAMES,
                {"predicate": AT_RISK, "count": 1, "error_class": "invalid_value"},
                planner,
            )
        self.assertEqual(planner.calls, [])

    def test_prior_attempt_is_a_count_or_a_rejection(self) -> None:
        payload = {"predicate": AT_RISK, "count": 2147}
        self.assertEqual(PriorAttempt.model_validate(payload).count, 2147)
        with self.assertRaises(ValidationError):
            PriorAttempt.model_validate({"predicate": AT_RISK})


if __name__ == "__main__":
    unittest.main()
