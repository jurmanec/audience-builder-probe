# Run a template intent

The `intent` argument is a label for one audience segment. The label corresponds to the rules already used to build that audience. In this system those rules are a predicate. Adobe Experience Platform uses "audience" for this label and "rules" for the predicate.

Writes an audience file only when the intent is one of `at-risk renewal`, `heavy-use upgrade`, or `lapsed video offer`. Any other intent writes no audience file.

```sh
.venv/bin/python -m builder.template_runner "at-risk renewal" --out out/audience.json
```

Exit `0` prints the audience path. That file is a draft audience for month-to-month households with at least 12 months of tenure and at least 2 recent support contacts:

```json
{
  "predicates": {
    "all": [
      {
        "field": "tenure_months",
        "op": "gte",
        "value": 12
      },
      {
        "field": "contract_status",
        "op": "eq",
        "value": "month_to_month"
      },
      {
        "field": "support_contacts_90d",
        "op": "gte",
        "value": 2
      }
    ]
  },
  "estimated_size": 2147,
  "status": "draft"
}
```

The same command with `"heavy-use upgrade"` writes a draft of size 440. `"lapsed video offer"` writes a draft of size 1,052.

Each count appends one line to `logs/tool.jsonl`. A successful at-risk run looks like this. `run_id` and `duration_ms` change on every call.

```json
{
  "run_id": "5d31e8be34054f91bb9d244b3ba58bcc",
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
  "duration_ms": 36.46,
  "count": 2147
}
```

An unknown intent stops before any file exists:

```sh
.venv/bin/python -m builder.template_runner "target by age" --out out/audience.json
```

That exits `2` and leaves no `out/audience.json`. The same happens for the five gold objectives that have no template (`g04` through `g08`). The eval harness checks this by passing each gold objective's `template_intent` into the runner. The runner itself never opens `eval/gold.json`.

The count tool can also be called directly. A predicate that names `age_years` is rejected before any row is counted:

```python
from tools import count_audience

count_audience({
    "predicate": {"all": [{"field": "age_years", "op": "gte", "value": 18}]}
})
```

The result is `count` null and `error_class` `forbidden_field`. The log line has `"outcome": "rejection"` and the same error class. Nothing is written except that log line.
