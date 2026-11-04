"""Generate the synthetic household table from the catalog.

The proof file stays untouched. A fixed seed rebuilds this file exactly.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from corpus.load_catalog import CATALOG_PATH, validate_catalog
from corpus.load_households import load_households
from corpus.validate_households import ID_FIELD, validate_households

ROOT = Path(__file__).resolve().parent
POPULATION_PATH = ROOT / "households.json"
ROW_COUNT = 5000
SEED = 20261102


def generate_rows(attributes: list[dict], count: int = ROW_COUNT, seed: int = SEED) -> list[dict]:
    if count < 1:
        raise ValueError("row count must be at least 1")
    usable = [attribute for attribute in attributes if attribute["usable"]]
    rng = random.Random(seed)
    return [_row(rng, usable, index) for index in range(1, count + 1)]


def write_population(
    path: Path = POPULATION_PATH,
    catalog_path: Path = CATALOG_PATH,
    count: int = ROW_COUNT,
    seed: int = SEED,
) -> list[dict]:
    attributes = validate_catalog(json.loads(catalog_path.read_text()))
    rows = generate_rows(attributes, count, seed)
    validate_households(rows, attributes)
    path.write_text(json.dumps(rows, indent=2) + "\n")
    return rows


def _row(rng: random.Random, usable: list[dict], index: int) -> dict:
    row: dict = {ID_FIELD: f"h{index:05d}"}
    for attribute in usable:
        row[attribute["name"]] = _value(rng, attribute)
    return row


def _value(rng: random.Random, attribute: dict) -> object:
    value_type = attribute["type"]
    if value_type == "int":
        return rng.randint(attribute["min"], attribute["max"])
    if value_type == "enum":
        return rng.choice(attribute["values"])
    return rng.choice((True, False))


def main() -> None:
    rows = write_population()
    loaded = load_households(POPULATION_PATH)
    print(f"wrote {len(rows)} seed {SEED}")
    print(f"household {loaded}")


if __name__ == "__main__":
    main()
