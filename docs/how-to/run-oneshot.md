# Run a one-shot

Writes an audience file only when one model call and one count return a draft audience. A miss writes no audience file and no brief file. The command does not approve an audience.

```sh
.venv/bin/python -m builder.oneshot_runner "Month-to-month households with at least a year of tenure and recent support contact." --out out/audience.json
```

Exit `0` prints the audience path. Exit `2` means nothing was written. The default model is `grok-4.7`. Put the key in `.env` in the project root as `XAI_API_KEY=...`. That file is not committed. A missing key makes no request and exits `2`. There is no second call.

Tool calls are appended to `logs/tool.jsonl`.

A scripted predicate skips the model. This one counts the at-risk audience and returns a draft of size 2,147. It still writes no file; `builder.oneshot_runner` is what writes.

```python
from builder.oneshot import run_oneshot
from builder.planner import ScriptedPlanner

at_risk = {
    "all": [
        {"field": "tenure_months", "op": "gte", "value": 12},
        {"field": "contract_status", "op": "eq", "value": "month_to_month"},
        {"field": "support_contacts_90d", "op": "gte", "value": 2},
    ]
}
audience = run_oneshot(
    "Month-to-month households with at least a year of tenure and recent support contact.",
    ScriptedPlanner([at_risk]),
    run_id="oneshot-example",
)
```

```json
{
  "predicates": {
    "all": [
      {"field": "tenure_months", "op": "gte", "value": 12},
      {"field": "contract_status", "op": "eq", "value": "month_to_month"},
      {"field": "support_contacts_90d", "op": "gte", "value": 2}
    ]
  },
  "estimated_size": 2147,
  "status": "draft"
}
```

The same `run_id` is on both tool lines. `duration_ms` changes on every call.

```json
{"run_id": "oneshot-example", "tool": "list_usable_attributes", "arguments": {}, "outcome": "pass", "duration_ms": 0.715}
{"run_id": "oneshot-example", "tool": "count_audience", "arguments": {"predicate": {"all": [{"field": "tenure_months", "op": "gte", "value": 12}, {"field": "contract_status", "op": "eq", "value": "month_to_month"}, {"field": "support_contacts_90d", "op": "gte", "value": 2}]}}, "outcome": "count", "duration_ms": 24.455, "count": 2147}
```

A forbidden field returns `None` after one rejection:

```python
audience = run_oneshot(
    "Households targeted by age.",
    ScriptedPlanner([{"all": [{"field": "age_years", "op": "gte", "value": 18}]}]),
    run_id="oneshot-age",
)
```

```json
{"run_id": "oneshot-age", "tool": "count_audience", "arguments": {"predicate": {"all": [{"field": "age_years", "op": "gte", "value": 18}]}}, "outcome": "rejection", "duration_ms": 0.145, "error_class": "forbidden_field"}
```
