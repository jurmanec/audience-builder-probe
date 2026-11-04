"""Load corpus/catalog.json into DuckDB.

The JSON file is the catalog contract. intake.duckdb is rebuilt from it.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "catalog.json"
DB_PATH = ROOT / "intake.duckdb"

ALLOWED_KEYS = {"name", "type", "usable", "operators", "min", "max", "values"}
OPERATORS_BY_TYPE = {
    "int": {"eq", "gte", "lte", "between"},
    "enum": {"eq", "in"},
    "bool": {"eq"},
}


class CatalogError(ValueError):
    """The catalog file breaks its own contract."""


def validate_catalog(data: dict) -> list[dict]:
    attributes = data.get("attributes")
    if not isinstance(attributes, list) or not attributes:
        raise CatalogError("catalog must contain a non-empty attributes list")

    seen: set[str] = set()
    normalized: list[dict] = []
    for index, raw in enumerate(attributes):
        normalized.append(_normalize_attribute(index, raw, seen))
    return normalized


def load_catalog(catalog_path: Path = CATALOG_PATH, db_path: Path = DB_PATH) -> list[tuple]:
    data = json.loads(catalog_path.read_text())
    attributes = validate_catalog(data)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(db_path))
    try:
        _replace_tables(connection, attributes)
        counts = _usable_counts(connection)
    finally:
        connection.close()
    return counts


def _normalize_attribute(index: int, raw: object, seen: set[str]) -> dict:
    label = f"attributes[{index}]"
    if not isinstance(raw, dict):
        raise CatalogError(f"{label} must be an object")

    unexpected = set(raw) - ALLOWED_KEYS
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise CatalogError(f"{label} has unexpected keys: {names}")

    name = raw.get("name")
    value_type = raw.get("type")
    usable = raw.get("usable")
    operators = raw.get("operators")

    if not isinstance(name, str) or not name.isidentifier() or name.lower() != name:
        raise CatalogError(f"{label} needs a lowercase identifier name")
    if name in seen:
        raise CatalogError(f"{label} duplicates attribute {name}")
    seen.add(name)
    label = name

    if value_type not in OPERATORS_BY_TYPE:
        raise CatalogError(f"{label} type must be int, enum, or bool")
    if not isinstance(usable, bool):
        raise CatalogError(f"{label} usable must be a boolean")
    if not isinstance(operators, list) or not all(isinstance(op, str) for op in operators):
        raise CatalogError(f"{label} operators must be a list of strings")
    if len(operators) != len(set(operators)):
        raise CatalogError(f"{label} repeats an operator")

    unknown_ops = set(operators) - OPERATORS_BY_TYPE[value_type]
    if unknown_ops:
        names = ", ".join(sorted(unknown_ops))
        raise CatalogError(f"{label} does not allow operators: {names}")

    minimum = raw.get("min")
    maximum = raw.get("max")
    values = raw.get("values")
    if not usable:
        if operators or minimum is not None or maximum is not None or values:
            raise CatalogError(f"{label} is forbidden and must have no operators, bounds, or values")
        return {
            "name": name,
            "type": value_type,
            "usable": False,
            "operators": [],
            "min": None,
            "max": None,
            "values": [],
        }

    if not operators:
        raise CatalogError(f"{label} is usable and needs at least one operator")

    if value_type == "int":
        if not isinstance(minimum, int) or isinstance(minimum, bool):
            raise CatalogError(f"{label} needs an integer min")
        if not isinstance(maximum, int) or isinstance(maximum, bool):
            raise CatalogError(f"{label} needs an integer max")
        if minimum > maximum:
            raise CatalogError(f"{label} min must be less than or equal to max")
        if values is not None:
            raise CatalogError(f"{label} is an int and must not list values")
        enum_values: list[str] = []
    elif value_type == "enum":
        if minimum is not None or maximum is not None:
            raise CatalogError(f"{label} is an enum and must not set min or max")
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value for value in values)
        ):
            raise CatalogError(f"{label} needs a non-empty list of enum values")
        if len(values) != len(set(values)):
            raise CatalogError(f"{label} repeats an enum value")
        minimum = None
        maximum = None
        enum_values = values
    else:
        if minimum is not None or maximum is not None or values is not None:
            raise CatalogError(f"{label} is a bool and must not set min, max, or values")
        minimum = None
        maximum = None
        enum_values = []

    return {
        "name": name,
        "type": value_type,
        "usable": True,
        "operators": operators,
        "min": minimum,
        "max": maximum,
        "values": enum_values,
    }


def _replace_tables(connection: duckdb.DuckDBPyConnection, attributes: list[dict]) -> None:
    connection.execute("DROP TABLE IF EXISTS enum_value")
    connection.execute("DROP TABLE IF EXISTS attribute_operator")
    connection.execute("DROP TABLE IF EXISTS attribute")
    connection.execute(
        """
        CREATE TABLE attribute (
          name VARCHAR PRIMARY KEY,
          value_type VARCHAR NOT NULL,
          usable BOOLEAN NOT NULL,
          min_value INTEGER,
          max_value INTEGER
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE attribute_operator (
          attribute_name VARCHAR NOT NULL REFERENCES attribute(name),
          operator VARCHAR NOT NULL,
          PRIMARY KEY (attribute_name, operator)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE enum_value (
          attribute_name VARCHAR NOT NULL REFERENCES attribute(name),
          value VARCHAR NOT NULL,
          PRIMARY KEY (attribute_name, value)
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO attribute (name, value_type, usable, min_value, max_value)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (row["name"], row["type"], row["usable"], row["min"], row["max"])
            for row in attributes
        ],
    )
    connection.executemany(
        """
        INSERT INTO attribute_operator (attribute_name, operator)
        VALUES (?, ?)
        """,
        [(row["name"], operator) for row in attributes for operator in row["operators"]],
    )
    connection.executemany(
        """
        INSERT INTO enum_value (attribute_name, value)
        VALUES (?, ?)
        """,
        [(row["name"], value) for row in attributes for value in row["values"]],
    )


def _usable_counts(connection: duckdb.DuckDBPyConnection) -> list[tuple]:
    return connection.execute(
        """
        SELECT usable, count(*) AS n
        FROM attribute
        GROUP BY usable
        ORDER BY usable DESC
        """
    ).fetchall()


def main() -> None:
    counts = load_catalog()
    print("usable\tn")
    for usable, count in counts:
        print(f"{usable}\t{count}")


if __name__ == "__main__":
    main()
