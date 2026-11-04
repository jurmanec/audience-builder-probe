"""One model call and one count.

A count from 1 through 2,500 returns a draft audience. An empty count, a count
above 2,500, a rejection, or a response that is not a predicate returns
nothing. This module does not revise, writes no file, and does not read the
gold set.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from builder.planner import Planner, PlannerError, XAIOneShot, plan_predicate
from builder.schemas import Audience, CountResult
from builder.tools import LOG_PATH, count_audience, list_usable_attributes

BROAD_ABOVE = 2500


def run_oneshot(
    objective: str,
    planner: Planner | None = None,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> Audience | None:
    chosen = planner if planner is not None else XAIOneShot()
    shared_run = run_id or uuid.uuid4().hex
    shared_log = log_path or LOG_PATH
    listed = list_usable_attributes(log_path=shared_log, run_id=shared_run)
    try:
        predicate = plan_predicate(objective, listed.names, planner=chosen)
    except PlannerError:
        return None
    result = count_audience(
        {"predicate": predicate.model_dump()},
        log_path=shared_log,
        run_id=shared_run,
    )
    if not _accepted(result):
        return None
    return Audience.model_validate(
        {
            "predicates": predicate.model_dump(),
            "estimated_size": result.count,
            "status": "draft",
        }
    )


def _accepted(result: CountResult) -> bool:
    return result.count is not None and 1 <= result.count <= BROAD_ABOVE
