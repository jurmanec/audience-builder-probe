"""Write an audience file only when a template intent matches.

A miss writes nothing. This module does not write a brief.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from builder.templates import run_template


def write_audience(intent: str | None, destination: Path) -> bool:
    audience = run_template(intent)
    if audience is None:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(audience.model_dump_json(indent=2) + "\n")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one template intent.")
    parser.add_argument("intent", nargs="?", default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if write_audience(args.intent, args.out):
        print(args.out)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
