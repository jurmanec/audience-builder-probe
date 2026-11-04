# Attribute catalog suggestion

Recorded before `corpus/catalog.json` was created. This is the suggestion as accepted for the first count, not a later revision of the catalog.

Use a short subscription-household catalog, an AND-only predicate, and three examples that can later become the template intents. Every usable field is required on each row, so the first count query does not need null handling.

## Catalog

Forbidden fields are listed here and are not columns. A predicate that names one is rejected before any query.

| Field | Type | Operators | Values | Usable |
|---|---|---|---|---|
| `tenure_months` | int | `gte`, `lte`, `between` | 0–240 | yes |
| `region` | enum | `eq`, `in` | `north`, `central`, `south`, `west` | yes |
| `internet_tier` | enum | `eq`, `in` | `none`, `basic`, `standard`, `gig` | yes |
| `mobile_lines` | int | `eq`, `gte`, `lte` | 0–8 | yes |
| `video_subscribed` | bool | `eq` | `true`, `false` | yes |
| `contract_status` | enum | `eq`, `in` | `month_to_month`, `in_term` | yes |
| `monthly_bill_cents` | int | `gte`, `lte`, `between` | 0–40000 | yes |
| `data_gb_30d` | int | `gte`, `lte`, `between` | 0–2000 | yes |
| `support_contacts_90d` | int | `gte`, `lte` | 0–20 | yes |
| `autopay` | bool | `eq` | `true`, `false` | yes |
| `days_since_last_offer` | int | `gte`, `lte` | 0–999 | yes |
| `age_years` | int | — | — | no |
| `household_income_cents` | int | — | — | no |
| `ethnicity` | enum | — | — | no |

`between` takes `[low, high]`, inclusive. `in` takes a list. Add further usable fields before the M0 freeze if a gold objective cannot be expressed. Leave this set alone for the first count.

## Predicate

A predicate is a single `all` list. Every entry must match.

```json
{
  "all": [
    { "field": "tenure_months", "op": "gte", "value": 12 },
    { "field": "contract_status", "op": "eq", "value": "month_to_month" }
  ]
}
```

## Three examples

At-risk renewal: tenure at least 12 months, month-to-month, and at least two support contacts in 90 days.

```json
{
  "all": [
    { "field": "tenure_months", "op": "gte", "value": 12 },
    { "field": "contract_status", "op": "eq", "value": "month_to_month" },
    { "field": "support_contacts_90d", "op": "gte", "value": 2 }
  ]
}
```

Heavy-use upgrade in one region: region `north`, internet `none` or `basic`, and at least 500 GB in 30 days.

```json
{
  "all": [
    { "field": "region", "op": "eq", "value": "north" },
    { "field": "internet_tier", "op": "in", "value": ["none", "basic"] },
    { "field": "data_gb_30d", "op": "gte", "value": 500 }
  ]
}
```

Lapsed video offer: video subscribed, autopay off, and at least 180 days since the last offer.

```json
{
  "all": [
    { "field": "video_subscribed", "op": "eq", "value": true },
    { "field": "autopay", "op": "eq", "value": false },
    { "field": "days_since_last_offer", "op": "gte", "value": 180 }
  ]
}
```

## Audience record

Written only after the predicate validates and the count succeeds. Status starts as `draft`. The brief step later requires `approved`.

```json
{
  "predicates": { "all": [] },
  "estimated_size": 0,
  "status": "draft"
}
```
