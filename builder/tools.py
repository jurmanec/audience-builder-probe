"""Typed tools over the frozen catalog, household file, and campaign library.

Each call appends one JSON log record. These tools do not choose a template
and do not write an audience file.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from pydantic import ValidationError

from corpus.count_predicate import PredicateError, count_predicate, validate_predicate
from corpus.generate_households import POPULATION_PATH
from corpus.load_catalog import CATALOG_PATH, validate_catalog
from builder.schemas import CampaignList, CatalogResult, CountInput, CountResult

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "tool.jsonl"
CAMPAIGNS_PATH = Path(__file__).resolve().parents[1] / "corpus" / "campaigns.json"


def count_audience(
    payload: CountInput | dict,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> CountResult:
    started = time.perf_counter()
    arguments, result = _count(payload)
    _log(
        tool="count_audience",
        arguments=arguments,
        outcome="rejection" if result.error_class else "count",
        duration_ms=_duration_ms(started),
        run_id=run_id or uuid.uuid4().hex,
        log_path=log_path or LOG_PATH,
        count=result.count,
        error_class=result.error_class,
    )
    return result


def list_usable_attributes(
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> CatalogResult:
    started = time.perf_counter()
    names = [attribute["name"] for attribute in _attributes() if attribute["usable"]]
    result = CatalogResult(names=names)
    _log(
        tool="list_usable_attributes",
        arguments={},
        outcome="pass",
        duration_ms=_duration_ms(started),
        run_id=run_id or uuid.uuid4().hex,
        log_path=log_path or LOG_PATH,
    )
    return result


def list_campaigns(
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> CampaignList:
    started = time.perf_counter()
    result = CampaignList.model_validate({"campaigns": json.loads(CAMPAIGNS_PATH.read_text())})
    _log(
        tool="list_campaigns",
        arguments={},
        outcome="pass",
        duration_ms=_duration_ms(started),
        run_id=run_id or uuid.uuid4().hex,
        log_path=log_path or LOG_PATH,
    )
    return result


def _count(payload: CountInput | dict) -> tuple[dict, CountResult]:
    try:
        incoming = payload if isinstance(payload, CountInput) else CountInput.model_validate(payload)
    except ValidationError:
        arguments = payload if isinstance(payload, dict) else {}
        return arguments, CountResult(error_class="invalid_predicate")

    arguments = incoming.model_dump()
    attributes = _attributes()
    predicate = incoming.predicate.model_dump()
    try:
        validate_predicate(predicate, attributes)
    except PredicateError as error:
        return arguments, CountResult(error_class=_error_class(str(error)))

    rows = json.loads(POPULATION_PATH.read_text())
    return arguments, CountResult(count=count_predicate(predicate, rows, attributes))


def _log(
    *,
    tool: str,
    arguments: dict,
    outcome: str,
    duration_ms: float,
    run_id: str,
    log_path: Path,
    count: int | None = None,
    error_class: str | None = None,
) -> None:
    record = {
        "run_id": run_id,
        "tool": tool,
        "arguments": arguments,
        "outcome": outcome,
        "duration_ms": duration_ms,
    }
    if count is not None:
        record["count"] = count
    if error_class is not None:
        record["error_class"] = error_class
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _duration_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def _attributes() -> list[dict]:
    return validate_catalog(json.loads(CATALOG_PATH.read_text()))


def _error_class(message: str) -> str:
    if "not usable" in message:
        return "forbidden_field"
    if "not in the catalog" in message:
        return "unknown_field"
    if "does not allow operator" in message:
        return "invalid_operator"
    if "only an all list" in message or message.startswith("all must") or "must contain field" in message:
        return "invalid_predicate"
    return "invalid_value"
