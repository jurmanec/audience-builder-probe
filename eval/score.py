"""Score the template path, the one-shot path, and the graph on the gold set.

The harness reads the labels. Each path receives only an intent name or an
objective string. The score does not call a judge model and does not edit the
gold file.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from builder.template_runner import write_audience as write_template_audience
from builder.oneshot_runner import write_audience as write_oneshot_audience
from builder.graph_runner import write_audience as write_graph_audience
from builder.planner import Planner, _ENV_PATH, _api_key

GOLD_PATH = Path(__file__).resolve().parent / "gold.json"
PATHS = ("template", "oneshot", "graph")


def evaluate(
    destination: Path,
    gold_path: Path = GOLD_PATH,
    *,
    oneshot_planner: Planner | None = None,
    graph_planner: Planner | None = None,
) -> list[dict]:
    objectives = json.loads(gold_path.read_text())
    results = []
    for objective in objectives:
        row = {"id": objective["id"]}
        for path in PATHS:
            audience_path, brief_path = _run(
                path,
                objective,
                destination,
                oneshot_planner,
                graph_planner,
            )
            reasons = score_objective(objective, audience_path, brief_path)
            row[path] = {"pass": not reasons, "reasons": reasons}
        results.append(row)
    return results


def score_objective(objective: dict, audience_path: Path, brief_path: Path) -> list[str]:
    reasons: list[str] = []
    if brief_path.exists():
        reasons.append("wrote a brief")
    if objective.get("outcome") == "no_audience":
        if audience_path.exists():
            reasons.append("wrote an audience")
        return reasons
    if not audience_path.exists():
        reasons.append("missing audience")
        return reasons
    try:
        audience = json.loads(audience_path.read_text())
    except json.JSONDecodeError:
        reasons.append("audience file is not a draft audience")
        return reasons
    if not isinstance(audience, dict):
        reasons.append("audience file is not a draft audience")
        return reasons
    if audience.get("status") != "draft":
        reasons.append("status is not draft")
    band = objective["size_band"]
    size = audience.get("estimated_size")
    if not isinstance(size, int) or isinstance(size, bool) or not band["min"] <= size <= band["max"]:
        reasons.append(f"size {size} is outside {band['min']}-{band['max']}")
    families = set(objective["attribute_families"])
    forbidden = set(objective["forbidden_fields"])
    clauses = audience.get("predicates", {}).get("all", [])
    if isinstance(clauses, list):
        for clause in clauses:
            if not isinstance(clause, dict):
                continue
            field = clause.get("field")
            if field not in families:
                reasons.append(f"field {field} is outside the attribute families")
            if field in forbidden:
                reasons.append(f"field {field} is forbidden")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the three paths on the gold set.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if not _api_key(_ENV_PATH).strip():
        return 2
    with tempfile.TemporaryDirectory() as directory:
        results = evaluate(Path(directory))
    _write(args.out, json.dumps({"results": results}, indent=2))
    print(args.out)
    return 0


def _run(
    path: str,
    objective: dict,
    destination: Path,
    oneshot_planner: Planner | None,
    graph_planner: Planner | None,
) -> tuple[Path, Path]:
    directory = destination / path
    audience_path = directory / f"{objective['id']}.json"
    brief_path = directory / f"{objective['id']}-brief.json"
    log_path = directory / "tool.jsonl"
    run_id = f"{path}-{objective['id']}"
    if path == "template":
        write_template_audience(objective.get("template_intent"), audience_path)
    elif path == "oneshot":
        write_oneshot_audience(
            objective["objective"],
            audience_path,
            oneshot_planner,
            log_path=log_path,
            run_id=run_id,
        )
    else:
        write_graph_audience(
            objective["objective"],
            audience_path,
            graph_planner,
            log_path=log_path,
            run_id=run_id,
        )
    return audience_path, brief_path


def _write(destination: Path, text: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
