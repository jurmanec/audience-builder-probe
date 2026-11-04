"""Write an audience file only when the graph returns one.

A miss writes nothing. This module does not approve an audience and does not
write a brief unless the caller asks for one after approval.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from builder.brief import CampaignChooser, draft_brief
from builder.graph import run_graph
from builder.planner import Planner
from builder.schemas import Audience


def write_audience(
    objective: str | None,
    destination: Path,
    planner: Planner | None = None,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> bool:
    audience = run_graph(objective or "", planner, log_path=log_path, run_id=run_id)
    if audience is None:
        return False
    _write(destination, audience.model_dump_json(indent=2))
    return True


def write_brief(
    audience: Audience | dict,
    destination: Path,
    chooser: CampaignChooser | None = None,
    *,
    log_path: Path | None = None,
    run_id: str | None = None,
) -> bool:
    brief = draft_brief(audience, chooser, log_path=log_path, run_id=run_id)
    if brief is None:
        return False
    _write(destination, brief.model_dump_json(indent=2))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one graph objective.")
    parser.add_argument("objective", nargs="?", default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if write_audience(args.objective, args.out):
        print(args.out)
        return 0
    return 2


def _write(destination: Path, text: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
