"""Thin planner interface.

A caller supplies a planner. Tests use ScriptedPlanner. The default planner
is xAI model grok-4.7. The API key is read from the environment or from .env
in the project root. A missing key makes no request.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from corpus.load_catalog import CATALOG_PATH, CatalogError, validate_catalog
from builder.schemas import Predicate, PriorAttempt

MODEL_ID = "grok-4.7"
API_URL = "https://api.x.ai/v1/chat/completions"
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
Transport = Callable[[dict], str]

PREDICATE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["all"],
    "properties": {
        "all": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "op", "value"],
                "properties": {
                    "field": {"type": "string"},
                    "op": {"type": "string"},
                    "value": {
                        "anyOf": [
                            {"type": "integer"},
                            {"type": "boolean"},
                            {"type": "string"},
                            {"type": "array", "items": {"type": "integer"}},
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    },
                },
            },
        }
    },
}

Planner = Callable[[str, list[str], PriorAttempt | None], Predicate | dict]


class PlannerError(ValueError):
    """The planner input or its predicate broke the contract."""


class ScriptedPlanner:
    """Return predicates in order and record each call."""

    def __init__(self, predicates: list[dict]) -> None:
        self._predicates = [Predicate.model_validate(predicate) for predicate in predicates]
        self.calls: list[tuple[str, list[str], PriorAttempt | None]] = []

    def __call__(
        self,
        objective: str,
        usable_names: list[str],
        prior: PriorAttempt | None,
    ) -> Predicate:
        self.calls.append((objective, list(usable_names), prior))
        if not self._predicates:
            raise PlannerError("scripted planner has no predicate left")
        return self._predicates.pop(0)


class XAIPlanner:
    """Default provider. grok-4.7 is the model id for the first live call."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        api_key: str | None = None,
        transport: Transport | None = None,
        env_path: Path | None = None,
    ) -> None:
        self.model_id = model_id
        self._api_key = api_key
        self._transport = transport
        self._env_path = _ENV_PATH if env_path is None else env_path

    def __call__(
        self,
        objective: str,
        usable_names: list[str],
        prior: PriorAttempt | None,
    ) -> dict:
        payload = planner_request(self.model_id, objective, usable_names, prior)
        return _complete(payload, self._api_key, self._transport, self._env_path)


def plan_predicate(
    objective: str,
    usable_names: list[str],
    prior: PriorAttempt | dict | None = None,
    planner: Planner | None = None,
) -> Predicate:
    objective = _objective(objective)
    names = _names(usable_names)
    attempt = _prior(prior)
    chosen = planner if planner is not None else XAIPlanner()
    try:
        return Predicate.model_validate(chosen(objective, names, attempt))
    except ValidationError as error:
        raise PlannerError("planner predicate failed validation") from error
    except PlannerError:
        raise


def _objective(objective: str) -> str:
    if not isinstance(objective, str) or not objective.strip():
        raise PlannerError("objective is required")
    return objective.strip()


def _names(usable_names: list[str]) -> list[str]:
    if (
        not isinstance(usable_names, list)
        or not usable_names
        or any(not isinstance(name, str) or not name.strip() for name in usable_names)
        or len(usable_names) != len(set(usable_names))
    ):
        raise PlannerError("usable attribute names must be unique and non-empty")
    return usable_names


def planner_request(
    model_id: str,
    objective: str,
    usable_names: list[str],
    prior: PriorAttempt | None,
) -> dict:
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return one audience predicate. Use only the listed attributes. "
                    "The predicate has one key, all, and all is a non-empty list of clauses. "
                    "Each clause has field, op, and value. "
                    "Use only an operator listed for that field. "
                    "For an enum, value must be one of the listed values exactly."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "objective": objective,
                        "attributes": _attribute_guide(usable_names),
                        "prior_attempt": None if prior is None else prior.model_dump(),
                    }
                ),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "predicate",
                "strict": True,
                "schema": PREDICATE_SCHEMA,
            },
        },
    }


def _attribute_guide(names: list[str]) -> list[dict]:
    try:
        attributes = validate_catalog(json.loads(CATALOG_PATH.read_text()))
    except (OSError, json.JSONDecodeError, CatalogError) as error:
        raise PlannerError("catalog could not be read") from error
    by_name = {item["name"]: item for item in attributes}
    guide: list[dict] = []
    for name in names:
        item = by_name.get(name)
        if item is None or not item["usable"]:
            raise PlannerError("usable attribute names must come from the catalog")
        entry: dict = {
            "name": item["name"],
            "type": item["type"],
            "operators": item["operators"],
        }
        if item["type"] == "enum":
            entry["values"] = item["values"]
        elif item["type"] == "int":
            entry["min"] = item["min"]
            entry["max"] = item["max"]
        guide.append(entry)
    return guide


def _api_key(env_path: Path) -> str:
    _load_env_file(env_path)
    return os.environ.get("XAI_API_KEY", "")


def _load_env_file(path: Path) -> None:
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        name, separator, value = line.partition("=")
        if not separator:
            continue
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if name and name not in os.environ:
            os.environ[name] = value


def _post(payload: dict, api_key: str) -> str:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode()
    except urllib.error.HTTPError as error:
        raise PlannerError("xAI request failed") from error


def _predicate_from_response(body: str) -> dict:
    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        predicate = json.loads(content) if isinstance(content, str) else content
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise PlannerError("xAI response was not a predicate") from error
    if not isinstance(predicate, dict):
        raise PlannerError("xAI response was not a predicate")
    return predicate


class XAIOneShot:
    """One structured call. The request has no prior attempt."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        api_key: str | None = None,
        transport: Transport | None = None,
        env_path: Path | None = None,
    ) -> None:
        self.model_id = model_id
        self._api_key = api_key
        self._transport = transport
        self._env_path = _ENV_PATH if env_path is None else env_path

    def __call__(
        self,
        objective: str,
        usable_names: list[str],
        prior: PriorAttempt | None,
    ) -> dict:
        if prior is not None:
            raise PlannerError("one-shot call received a prior attempt")
        payload = oneshot_request(self.model_id, objective, usable_names)
        return _complete(payload, self._api_key, self._transport, self._env_path)


def oneshot_request(model_id: str, objective: str, usable_names: list[str]) -> dict:
    request = planner_request(model_id, objective, usable_names, None)
    user = json.loads(request["messages"][1]["content"])
    del user["prior_attempt"]
    request["messages"][1]["content"] = json.dumps(user)
    return request


def _complete(
    payload: dict,
    api_key: str | None,
    transport: Transport | None,
    env_path: Path,
) -> dict:
    key = api_key if api_key is not None else _api_key(env_path)
    if not key.strip():
        raise PlannerError("xAI API key is not set, so no live call is made")
    try:
        body = transport(payload) if transport is not None else _post(payload, key)
    except PlannerError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise PlannerError("xAI request failed") from error
    return _predicate_from_response(body)


def _prior(prior: PriorAttempt | dict | None) -> PriorAttempt | None:
    if prior is None:
        return None
    try:
        return prior if isinstance(prior, PriorAttempt) else PriorAttempt.model_validate(prior)
    except ValidationError as error:
        raise PlannerError("prior attempt failed validation") from error
