"""Plan, count, and revise.

The loop calls the existing tools. A count from 1 through 2,500 returns a
draft audience. An empty count, a count above 2,500, or a rejection is revised.
Three failed attempts return nothing. This module writes no file and does not
read the gold set.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal, TypedDict


from langgraph.graph import END, START, StateGraph

from builder.planner import Planner, PlannerError, XAIPlanner, plan_predicate
from builder.schemas import Audience, CountResult, PriorAttempt
from builder.tools import LOG_PATH, count_audience, list_usable_attributes

MAX_ATTEMPTS = 3
BROAD_ABOVE = 2500

NextStep = Literal["plan", "count", "__end__"]


class GraphState(TypedDict):
    objective: str
    run_id: str
    names: list[str]
    prior: dict | None
    predicate: dict | None
    attempts: int
    audience: dict | None


def run_graph(
    objective: str,
    planner: Planner | None = None,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> Audience | None:
    chosen = planner if planner is not None else XAIPlanner()
    app = _compile(chosen, log_path or LOG_PATH)
    final = app.invoke(
        {
            "objective": objective,
            "run_id": run_id or uuid.uuid4().hex,
            "names": [],
            "prior": None,
            "predicate": None,
            "attempts": 0,
            "audience": None,
        }
    )
    if final["audience"] is None:
        return None
    return Audience.model_validate(final["audience"])


def _compile(planner: Planner, log_path: Path):
    def catalog(state: GraphState) -> dict:
        listed = list_usable_attributes(log_path=log_path, run_id=state["run_id"])
        return {"names": listed.names}

    def plan(state: GraphState) -> dict:
        prior = None if state["prior"] is None else PriorAttempt.model_validate(state["prior"])
        try:
            predicate = plan_predicate(state["objective"], state["names"], prior, planner)
        except PlannerError:
            return {"predicate": None, "attempts": state["attempts"] + 1}
        return {"predicate": predicate.model_dump()}

    def count(state: GraphState) -> dict:
        result = count_audience(
            {"predicate": state["predicate"]},
            log_path=log_path,
            run_id=state["run_id"],
        )
        attempts = state["attempts"] + 1
        if _accepted(result):
            audience = Audience.model_validate(
                {
                    "predicates": state["predicate"],
                    "estimated_size": result.count,
                    "status": "draft",
                }
            )
            return {"attempts": attempts, "audience": audience.model_dump()}
        prior = PriorAttempt.model_validate(
            {
                "predicate": state["predicate"],
                "count": result.count,
                "error_class": result.error_class,
            }
        )
        return {"attempts": attempts, "audience": None, "prior": prior.model_dump()}

    graph = StateGraph(GraphState)
    graph.add_node("catalog", catalog)
    graph.add_node("plan", plan)
    graph.add_node("count", count)
    graph.add_edge(START, "catalog")
    graph.add_edge("catalog", "plan")
    graph.add_conditional_edges("plan", _after_plan)
    graph.add_conditional_edges("count", _after_count)
    return graph.compile()


def _accepted(result: CountResult) -> bool:
    return result.count is not None and 1 <= result.count <= BROAD_ABOVE

# attempts for predicate
# go to count if plan produced predicate
def _after_plan(state: GraphState) -> NextStep:
    if state["predicate"] is not None:
        return "count"
    if state["attempts"] >= MAX_ATTEMPTS: # 3
        return END # hard stop / end
    return "plan"

# 
def _after_count(state: GraphState) -> NextStep:
    if state["audience"] is not None:
        return END # end with audience
    if state["attempts"] >= MAX_ATTEMPTS: # 3
        return END # hard stop / end
    return "plan" # try to get predicate again
