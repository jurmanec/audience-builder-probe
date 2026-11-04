# Tool logs

Each tool call appends one JSON object to `logs/tool.jsonl`. The directory is gitignored. A line is enough to see which tool ran, what it was given, and whether it counted, passed, or rejected. OpenTelemetry is not part of this log.

Every record has `run_id`, `tool`, `arguments`, `outcome`, and `duration_ms`. A count also has `count`. A rejection also has `error_class`. `duration_ms` changes on every call. The template runner leaves `run_id` unset, so each call records its own id. A caller may pass one id for every call in a run; the examples below do that with `run-example`.

`outcome` is `count`, `pass`, or `rejection`. A rejection does not count rows and does not write an audience file. See [run a template intent](../how-to/run-template.md) for the command that produces a count.

## Count

`count_audience` accepted the at-risk predicate and counted 2,147 households.

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2}
      ]
    }
  },
  "outcome": "count",
  "duration_ms": 30.36,
  "count": 2147
}
```

## Pass

`list_usable_attributes` returned the 11 usable names. The record has no `count` and no `error_class`.

```json
{
  "run_id": "run-example",
  "tool": "list_usable_attributes",
  "arguments": {},
  "outcome": "pass",
  "duration_ms": 0.124
}
```

## Rejection

`error_class` is one of `forbidden_field`, `unknown_field`, `invalid_operator`, `invalid_predicate`, or `invalid_value`.

`age_years` is in the catalog and is not usable:

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": [
        {"field": "age_years", "op": "gte", "value": 18}
      ]
    }
  },
  "outcome": "rejection",
  "duration_ms": 0.214,
  "error_class": "forbidden_field"
}
```

`favorite_color` is not in the catalog:

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": [
        {"field": "favorite_color", "op": "eq", "value": "blue"}
      ]
    }
  },
  "outcome": "rejection",
  "duration_ms": 0.29,
  "error_class": "unknown_field"
}
```

`video_subscribed` allows `eq` only:

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": [
        {"field": "video_subscribed", "op": "gte", "value": true}
      ]
    }
  },
  "outcome": "rejection",
  "duration_ms": 0.141,
  "error_class": "invalid_operator"
}
```

An empty `all` list fails the predicate shape:

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": []
    }
  },
  "outcome": "rejection",
  "duration_ms": 0.122,
  "error_class": "invalid_predicate"
}
```

`tenure_months` stops at 240, so 241 is out of bounds:

```json
{
  "run_id": "run-example",
  "tool": "count_audience",
  "arguments": {
    "predicate": {
      "all": [
        {"field": "tenure_months", "op": "gte", "value": 241}
      ]
    }
  },
  "outcome": "rejection",
  "duration_ms": 0.183,
  "error_class": "invalid_value"
}
```
