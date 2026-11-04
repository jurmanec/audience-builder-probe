"""Count households that match one all-predicate.

The predicate is checked against the catalog before any row is counted.
"""

from __future__ import annotations


class PredicateError(ValueError):
    """A predicate breaks the catalog contract."""


def count_predicate(predicate: object, rows: list[dict], attributes: list[dict]) -> int:
    clauses = validate_predicate(predicate, attributes)
    return sum(1 for row in rows if all(_matches(row, clause) for clause in clauses))


def validate_predicate(predicate: object, attributes: list[dict]) -> list[dict]:
    if not isinstance(predicate, dict) or set(predicate) != {"all"}:
        raise PredicateError("predicate must contain only an all list")
    clauses = predicate["all"]
    if not isinstance(clauses, list) or not clauses:
        raise PredicateError("all must be a non-empty list")

    catalog = {attribute["name"]: attribute for attribute in attributes}
    return [_validate_clause(index, clause, catalog) for index, clause in enumerate(clauses)]


def _validate_clause(index: int, clause: object, catalog: dict[str, dict]) -> dict:
    label = f"all[{index}]"
    if not isinstance(clause, dict) or set(clause) != {"field", "op", "value"}:
        raise PredicateError(f"{label} must contain field, op, and value")

    field = clause["field"]
    op = clause["op"]
    value = clause["value"]
    if not isinstance(field, str) or field not in catalog:
        raise PredicateError(f"{label} field is not in the catalog")
    attribute = catalog[field]
    label = field
    if not attribute["usable"]:
        raise PredicateError(f"{label} is not usable")
    if op not in attribute["operators"]:
        raise PredicateError(f"{label} does not allow operator {op}")

    return {
        "field": field,
        "op": op,
        "value": _check_value(label, op, value, attribute),
    }


def _check_value(field: str, op: str, value: object, attribute: dict) -> object:
    value_type = attribute["type"]
    if value_type == "int":
        if op == "between":
            if (
                not isinstance(value, list)
                or len(value) != 2
                or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
            ):
                raise PredicateError(f"{field} between must be [low, high]")
            low, high = value
            if low > high:
                raise PredicateError(f"{field} between low must be less than or equal to high")
            _require_in_bounds(field, low, attribute)
            _require_in_bounds(field, high, attribute)
            return (low, high)
        if isinstance(value, bool) or not isinstance(value, int):
            raise PredicateError(f"{field} comparison must be an integer")
        _require_in_bounds(field, value, attribute)
        return value
    if value_type == "enum":
        allowed = set(attribute["values"])
        if op == "in":
            if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
                raise PredicateError(f"{field} in must be a non-empty list")
            unknown = sorted(set(value) - allowed)
            if unknown:
                raise PredicateError(f"{field} has unknown values: {', '.join(unknown)}")
            return value
        if not isinstance(value, str) or value not in allowed:
            raise PredicateError(f"{field} must be one of: {', '.join(attribute['values'])}")
        return value
    if not isinstance(value, bool):
        raise PredicateError(f"{field} must be a boolean")
    return value


def _require_in_bounds(field: str, value: int, attribute: dict) -> None:
    if value < attribute["min"] or value > attribute["max"]:
        raise PredicateError(
            f"{field} comparison must be between {attribute['min']} and {attribute['max']}"
        )


def _matches(row: dict, clause: dict) -> bool:
    actual = row[clause["field"]]
    op = clause["op"]
    value = clause["value"]
    if op == "eq":
        return actual == value
    if op == "gte":
        return actual >= value
    if op == "lte":
        return actual <= value
    if op == "in":
        return actual in value
    low, high = value
    return low <= actual <= high
