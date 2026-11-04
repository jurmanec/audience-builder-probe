# Predicate syntax

A predicate is the audience rule in this project. It selects households from `corpus/households.json`. The file is a JSON list of rows. It has no query language of its own. `corpus/count_predicate.py` checks the predicate against the catalog, then keeps a row when every clause matches.

The syntax is local to this project. Audience tools often use a field, an operator, and a value joined by AND. This JSON shape, these operator names, and the inclusive `between` rule are defined here. The live count does not parse SQL, JSONPath, or a published rules language.

## Shape

One object, one key. `all` is a non-empty list of clauses. Every clause has `field`, `op`, and `value`. Every clause must match. There is no `any` and no nesting.

```json
{
  "all": [
    { "field": "tenure_months", "op": "gte", "value": 12 },
    { "field": "contract_status", "op": "eq", "value": "month_to_month" },
    { "field": "support_contacts_90d", "op": "gte", "value": 2 }
  ]
}
```

The catalog in `corpus/catalog.json` decides which fields exist, which operators a field allows, and whether the field may be used. A clause that names a forbidden field, an unknown field, a disallowed operator, or an illegal value is rejected before any row is read.

| Operator | Value | Match |
| --- | --- | --- |
| `eq` | one integer, boolean, or enum string | equal |
| `gte` | one integer | greater than or equal |
| `lte` | one integer | less than or equal |
| `between` | `[low, high]` | inclusive range |
| `in` | a non-empty list | value is one of the list |

Booleans use only `eq`. An enum `eq` must be one listed value exactly. An enum `in` must be a non-empty list of listed values. An integer comparison must sit inside that field's min and max. `between` requires `low` less than or equal to `high`.

The model proposes this object and nothing else. Code counts the matching rows and writes `estimated_size`. Code sets `status` to `draft`.

## SQL in production

At the size of a national subscriber base, the count would run as SQL against a warehouse table. The at-risk predicate above is already written that way in `docs/how-to/sql-queries.md`:

```sql
SELECT count(*)
FROM household
WHERE tenure_months >= 12
  AND contract_status = 'month_to_month'
  AND support_contacts_90d >= 2;
```

The stored audience definition would remain the predicate. A compiler would emit the SQL after the catalog accepted the rule. The same definition can be compiled again for a count, an id export, or another warehouse. Analysts would still write SQL to build the household table and the attributes behind the catalog. A restricted SQL path sometimes exists for those analysts. The marketer-facing definition, and the only object a model would be allowed to propose, would stay the rule.

`corpus/intake.duckdb` holds a loaded copy of these rows for that kind of proof. The one-shot path and the graph do not open it. They call `count_predicate` on the JSON list.

## A telecom marketing platform

A large telecommunications marketing platform splits the work the same way.

The household table, sometimes called the subscriber or billing-account table, is the data. Each row is a household. Columns hold tenure, contract status, internet tier, video, mobile lines, bill, usage, and geography. It lives in a customer data platform or a warehouse, and it is far larger than this 5,000-row file.

The attribute catalog is the control. It lists the business name, the column, the type, the allowed operators, and whether marketing may target on that attribute. Sensitive fields stay out of the audience tool even when they exist elsewhere in the warehouse. This project's catalog is the small version: 11 usable attributes and 3 that are refused in code.

The segment builder is the syntax marketers see. They pick an attribute, an operator, and a value, and combine the clauses. The platform stores that rule, shows it, versions it, and checks it. The builder does not hand the marketer a SQL editor. When a count or an activation export is needed, the platform compiles the stored rule into a warehouse query.

This project follows that split at tracer scale. The predicate is the segment rule. The catalog is the allow-list. The JSON walk stands in for the compiled query. A draft audience still waits for a person to approve it before a brief can be written, which is the same gate a campaign team expects before a segment is activated.
