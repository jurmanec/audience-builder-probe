"""Run scripted graph cases over the gold objectives.

The harness reads the labels. The graph receives only an objective string.
"""

from __future__ import annotations

import json
from pathlib import Path

from builder.brief import ScriptedCampaignChooser
from builder.graph_runner import write_audience, write_brief
from builder.planner import ScriptedPlanner

GOLD_PATH = Path(__file__).resolve().parent / "gold.json"

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


def evaluate_graph(destination_dir: Path, gold_path: Path = GOLD_PATH) -> list[str]:
    objectives = {item["id"]: item for item in json.loads(gold_path.read_text())}
    log_path = destination_dir / "tool.jsonl"
    failures: list[str] = []
    countable = _countable(destination_dir, objectives["g01"], log_path)
    failures.extend(countable)
    failures.extend(_revised(destination_dir, objectives["g01"]["objective"], log_path))
    failures.extend(_closed(destination_dir, objectives["g07"], log_path))
    if not countable:
        failures.extend(_brief(destination_dir, log_path))
    return failures


def _countable(destination_dir: Path, objective: dict, log_path: Path) -> list[str]:
    audience_path = destination_dir / "g01.json"
    brief_path = destination_dir / "g01-brief.json"
    wrote = write_audience(
        objective["objective"],
        audience_path,
        ScriptedPlanner([AT_RISK]),
        log_path=log_path,
        run_id="g01",
    )
    if not wrote or not audience_path.exists() or brief_path.exists():
        return ["g01 did not write only an audience"]
    audience = json.loads(audience_path.read_text())
    band = objective["size_band"]
    size = audience["estimated_size"]
    if audience["status"] != "draft" or not band["min"] <= size <= band["max"]:
        return [f"g01 size {size} is outside {band['min']}-{band['max']}"]
    return []


def _revised(destination_dir: Path, objective: str, log_path: Path) -> list[str]:
    failures: list[str] = []
    empty = ScriptedPlanner([EMPTY, AT_RISK])
    broad = ScriptedPlanner([BROAD, AT_RISK])
    empty_path = destination_dir / "empty.json"
    broad_path = destination_dir / "broad.json"
    if not write_audience(objective, empty_path, empty, log_path=log_path, run_id="empty"):
        failures.append("empty count did not revise")
    elif empty.calls[1][2].count != 0 or (destination_dir / "empty-brief.json").exists():
        failures.append("empty count did not revise")
    if not write_audience(objective, broad_path, broad, log_path=log_path, run_id="broad"):
        failures.append("broad count did not revise")
    elif _broad_revision_missed(broad) or (destination_dir / "broad-brief.json").exists():
        failures.append("broad count did not revise")
    return failures


def _closed(destination_dir: Path, objective: dict, log_path: Path) -> list[str]:
    audience_path = destination_dir / "g07.json"
    brief_path = destination_dir / "g07-brief.json"
    wrote = write_audience(
        objective["objective"],
        audience_path,
        ScriptedPlanner([AGE, AGE, AGE]),
        log_path=log_path,
        run_id="g07",
    )
    if wrote or audience_path.exists() or brief_path.exists():
        return ["g07 wrote an audience"]
    return []


def _brief(destination_dir: Path, log_path: Path) -> list[str]:
    audience_path = destination_dir / "g01.json"
    audience = json.loads(audience_path.read_text())
    if audience["status"] != "draft":
        return ["g01 audience was approved by the runner"]
    draft_path = destination_dir / "g01-draft-brief.json"
    if write_brief(audience, draft_path, ScriptedCampaignChooser("c01"), log_path=log_path, run_id="draft-brief"):
        return ["draft audience wrote a brief"]
    if draft_path.exists():
        return ["draft audience wrote a brief"]
    audience["status"] = "approved"
    brief_path = destination_dir / "g01-brief.json"
    wrote = write_brief(
        audience,
        brief_path,
        ScriptedCampaignChooser("c01"),
        log_path=log_path,
        run_id="g01-brief",
    )
    if not wrote or not brief_path.exists():
        return ["approved audience did not write a brief"]
    brief = json.loads(brief_path.read_text())
    if brief["campaign_id"] != "c01" or brief["offer"] != "A bill credit for switching to paperless billing.":
        return ["brief did not copy the campaign"]
    if json.loads(audience_path.read_text())["status"] != "draft":
        return ["g01 audience was approved by the runner"]
    return []


def _broad_revision_missed(planner: ScriptedPlanner) -> bool:
    prior = planner.calls[1][2]
    return prior is None or prior.count is None or prior.count <= 2500
