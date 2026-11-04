# Attribute Catalog JSON Explanation

This JSON is a machine-readable **attribute catalog** (or attribute schema) used by a marketing/segmentation system. It defines the customer or household attributes available for filtering, audience building, and offer targeting—exactly the kind of governed catalog a telecom marketing platform uses.

## Structure Overview

The root object contains an `attributes` array. Each entry describes one attribute with:

| Field | Purpose |
|-------|---------|
| `name` | Unique identifier (e.g., `tenure_months`) |
| `type` | Data type: `int`, `enum`, or `bool` |
| `usable` | Governance flag — whether the attribute may currently be used in segments or campaigns |
| `operators` | Allowed comparison operators for building filters |
| `min` / `max` | Range constraints (for integers) |
| `values` | Allowed values (for enums) |

This catalog lets a UI, API, or rules engine know what filters are valid, what values are permitted, and which attributes are approved for use.

## Attribute Breakdown

### Usable attributes (typical telecom marketing fields)

- **`tenure_months`** (int, 0–240) — How long the customer has been with the company. Supports `gte`, `lte`, `between`. Useful for loyalty or win-back segments.
- **`region`** (enum) — Geographic region (`north`, `central`, `south`, `west`). Supports `eq`, `in`.
- **`internet_tier`** (enum) — Current broadband plan (`none`, `basic`, `standard`, `gig`). Supports upsell targeting.
- **`mobile_lines`** (int, 0–8) — Number of mobile lines. Supports exact match and range comparisons.
- **`video_subscribed`** (bool) — Whether the household has a TV/video package. Simple true/false filter.
- **`contract_status`** (enum) — `month_to_month` or `in_term`. Important for retention offers.
- **`monthly_bill_cents`** (int, 0–40,000) — Monthly spend in cents. Supports range filters for value-based targeting.
- **`data_gb_30d`** (int, 0–2,000) — Data usage in the last 30 days. Useful for unlimited-plan or speed-upgrade campaigns.
- **`support_contacts_90d`** (int, 0–20) — Recent support interactions. Can flag at-risk or high-touch customers.
- **`autopay`** (bool) — Whether the customer is on auto-pay.
- **`days_since_last_offer`** (int, 0–999) — Days since the last marketing offer. Helps with frequency capping or re-engagement.

### Non-usable attributes (governance / privacy controls)

- **`age_years`**, **`household_income_cents`**, **`ethnicity`** — Marked `"usable": false` with empty `operators` arrays. These are sensitive demographic attributes that the catalog explicitly disables, likely for privacy, regulatory, or policy reasons. The catalog still lists them so systems know they exist but cannot be activated for marketing use.

## Role in an Attribute Catalog

In the telecom marketing context:

1. **Segmentation engine** — A campaign tool reads this catalog to present only valid filters. A marketer can build a segment such as “tenure ≥ 24 months AND internet_tier IN (basic, standard) AND data_gb_30d ≥ 500 AND contract_status = month_to_month” because those operators and values are defined.
2. **Governance and compliance** — The `usable` flag is a runtime control. Sensitive fields are present for completeness or internal analytics but blocked from marketing activation.
3. **Validation** — The system can reject invalid queries (e.g., a `between` operator on an enum, or a value outside the declared range) before they hit the data warehouse or CDP.
4. **Consistency** — Downstream systems (addressable TV, email, app personalization, offer engines) all reference the same attribute definitions, names, and constraints.

In short, this JSON is the operational definition of the attribute catalog: it tells the marketing platform exactly which customer attributes exist, how they can be filtered, and which ones are currently approved for use.
