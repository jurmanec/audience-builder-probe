"""Run the template path over the gold set.

The harness reads the labels. The template path receives only an intent name.
"""

from __future__ import annotations

import json
from pathlib import Path

from builder.template_runner import write_audience

GOLD_PATH = Path(__file__).resolve().parent / "gold.json"


def evaluate_gold(destination_dir: Path, gold_path: Path = GOLD_PATH) -> list[str]:
    objectives = json.loads(gold_path.read_text())
    failures: list[str] = []
    for objective in objectives:
        objective_id = objective["id"]
        audience_path = destination_dir / f"{objective_id}.json"
        brief_path = destination_dir / f"{objective_id}-brief.json"
        wrote = write_audience(objective.get("template_intent"), audience_path)
        if objective.get("template_intent") is None:
            if wrote or audience_path.exists() or brief_path.exists():
                failures.append(f"{objective_id} wrote an audience")
            continue
        if not wrote or not audience_path.exists() or brief_path.exists():
            failures.append(f"{objective_id} did not write only an audience")
            continue
        audience = json.loads(audience_path.read_text())
        band = objective["size_band"]
        size = audience["estimated_size"]
        if audience["status"] != "draft" or not band["min"] <= size <= band["max"]:
            failures.append(f"{objective_id} size {size} is outside {band['min']}-{band['max']}")
    return failures
