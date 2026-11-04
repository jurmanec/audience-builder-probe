"""Load proof households into DuckDB after the catalog check.

The JSON file is the source of truth. This rebuilds the household table and
does not run an audience count.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

from corpus.load_catalog import CATALOG_PATH, DB_PATH, validate_catalog
from corpus.validate_households import HOUSEHOLDS_PATH, ID_FIELD, validate_households

COLUMN_TYPES = {"int": "INTEGER", "enum": "VARCHAR", "bool": "BOOLEAN"}
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*")


def load_households(
    households_path: Path = HOUSEHOLDS_PATH,
    catalog_path: Path = CATALOG_PATH,
    db_path: Path = DB_PATH,
) -> int:
    attributes = validate_catalog(json.loads(catalog_path.read_text()))
    rows = validate_households(json.loads(households_path.read_text()), attributes)
    usable = [attribute for attribute in attributes if attribute["usable"]]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(db_path))
    try:
        _replace_household(connection, usable, rows)
        count = connection.execute("SELECT count(*) FROM household").fetchone()[0]
    finally:
        connection.close()
    return count


def _replace_household(
    connection: duckdb.DuckDBPyConnection,
    usable: list[dict],
    rows: list[dict],
) -> None:
    columns = [_column_sql(attribute) for attribute in usable]
    column_names = [ID_FIELD, *[attribute["name"] for attribute in usable]]
    quoted = ", ".join(_quote(name) for name in column_names)
    placeholders = ", ".join(["?"] * len(column_names))

    connection.execute("DROP TABLE IF EXISTS household")
    connection.execute(
        f"""
        CREATE TABLE household (
          {_quote(ID_FIELD)} VARCHAR PRIMARY KEY,
          {", ".join(columns)}
        )
        """
    )
    connection.executemany(
        f"INSERT INTO household ({quoted}) VALUES ({placeholders})",
        [tuple(row[name] for name in column_names) for row in rows],
    )


def _column_sql(attribute: dict) -> str:
    return f"{_quote(attribute['name'])} {COLUMN_TYPES[attribute['type']]} NOT NULL"


def _quote(name: str) -> str:
    if not IDENTIFIER.fullmatch(name):
        raise ValueError(f"unsafe column name: {name}")
    return f'"{name}"'


def main() -> None:
    count = load_households()
    print(f"household {count}")


if __name__ == "__main__":
    main()
