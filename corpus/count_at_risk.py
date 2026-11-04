"""Run the hand-written at-risk proof query and compare it with the expected file.

This is one predicate, written as SQL. It does not compile a general predicate.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from corpus.load_catalog import DB_PATH

ROOT = Path(__file__).resolve().parent
EXPECTED_PATH = ROOT / "proof_at_risk_expected.json"

AT_RISK_SQL = """
SELECT household_id
FROM household
WHERE tenure_months >= 12
  AND contract_status = 'month_to_month'
  AND support_contacts_90d >= 2
ORDER BY household_id
"""


class AtRiskMismatch(RuntimeError):
    """The proof query did not return the ids recorded before SQL."""


def at_risk_ids(db_path: Path = DB_PATH) -> list[str]:
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        return [row[0] for row in connection.execute(AT_RISK_SQL).fetchall()]
    finally:
        connection.close()


def compare_at_risk(
    db_path: Path = DB_PATH,
    expected_path: Path = EXPECTED_PATH,
) -> list[str]:
    expected = json.loads(expected_path.read_text())
    found = at_risk_ids(db_path)
    if found != expected["household_ids"] or len(found) != expected["count"]:
        raise AtRiskMismatch(
            f"expected {expected['count']} ids {expected['household_ids']}, found {found}"
        )
    return found


def main() -> None:
    found = compare_at_risk()
    print(f"at-risk {len(found)}")
    for household_id in found:
        print(household_id)


if __name__ == "__main__":
    main()
