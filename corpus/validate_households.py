"""Check household rows against the attribute catalog.

This step does not write to DuckDB. A single bad row rejects the file.
"""

from __future__ import annotations

import json
from pathlib import Path

from corpus.load_catalog import CATALOG_PATH, validate_catalog

ROOT = Path(__file__).resolve().parent
HOUSEHOLDS_PATH = ROOT / "proof_households.json"
ID_FIELD = "household_id"


class HouseholdError(ValueError):
    """A household file breaks the catalog contract."""


def validate_households(rows: object, attributes: list[dict]) -> list[dict]:
    if not isinstance(rows, list) or not rows:
        raise HouseholdError("household file must contain a non-empty list")

    usable = [attribute for attribute in attributes if attribute["usable"]]
    forbidden = {attribute["name"] for attribute in attributes if not attribute["usable"]}
    usable_names = [attribute["name"] for attribute in usable]
    allowed = set(usable_names) | {ID_FIELD}

    seen: set[str] = set()
    normalized: list[dict] = []
    for index, raw in enumerate(rows):
        normalized.append(_normalize_row(index, raw, usable, forbidden, allowed, seen))
    return normalized


def validate_household_file(
    households_path: Path = HOUSEHOLDS_PATH,
    catalog_path: Path = CATALOG_PATH,
) -> list[dict]:
    attributes = validate_catalog(json.loads(catalog_path.read_text()))
    rows = json.loads(households_path.read_text())
    return validate_households(rows, attributes)


def _normalize_row(
    index: int,
    raw: object,
    usable: list[dict],
    forbidden: set[str],
    allowed: set[str],
    seen: set[str],
) -> dict:
    label = f"households[{index}]"
    if not isinstance(raw, dict):
        raise HouseholdError(f"{label} must be an object")

    household_id = raw.get(ID_FIELD)
    if not isinstance(household_id, str) or not household_id:
        raise HouseholdError(f"{label} needs a non-empty {ID_FIELD}")
    if household_id in seen:
        raise HouseholdError(f"{household_id} duplicates {ID_FIELD}")
    seen.add(household_id)
    label = household_id

    present = set(raw)
    blocked = sorted(present & forbidden)
    if blocked:
        names = ", ".join(blocked)
        raise HouseholdError(f"{label} uses forbidden attributes: {names}")

    unexpected = sorted(present - allowed)
    if unexpected:
        names = ", ".join(unexpected)
        raise HouseholdError(f"{label} has unexpected fields: {names}")

    missing = sorted(set(usable_names(usable)) - present)
    if missing:
        names = ", ".join(missing)
        raise HouseholdError(f"{label} is missing fields: {names}")

    normalized = {ID_FIELD: household_id}
    for attribute in usable:
        normalized[attribute["name"]] = _check_value(label, attribute, raw[attribute["name"]])
    return normalized


def usable_names(usable: list[dict]) -> list[str]:
    return [attribute["name"] for attribute in usable]


def _check_value(label: str, attribute: dict, value: object) -> object:
    name = attribute["name"]
    value_type = attribute["type"]
    if value_type == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise HouseholdError(f"{label}.{name} must be an integer")
        if value < attribute["min"] or value > attribute["max"]:
            raise HouseholdError(
                f"{label}.{name} must be between {attribute['min']} and {attribute['max']}"
            )
        return value
    if value_type == "enum":
        if not isinstance(value, str) or value not in attribute["values"]:
            allowed = ", ".join(attribute["values"])
            raise HouseholdError(f"{label}.{name} must be one of: {allowed}")
        return value
    if not isinstance(value, bool):
        raise HouseholdError(f"{label}.{name} must be a boolean")
    return value


def main() -> None:
    rows = validate_household_file()
    print(f"accepted {len(rows)}")


if __name__ == "__main__":
    main()
