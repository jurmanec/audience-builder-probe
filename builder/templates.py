"""Fixed predicates for the three template intents.

The caller passes an intent name. This module does not read the gold set
and does not write an audience file.
"""

from __future__ import annotations

from builder.schemas import Audience
from builder.tools import count_audience

INTENTS: dict[str, dict] = {
    "at-risk renewal": {
        "all": [
            {"field": "tenure_months", "op": "gte", "value": 12},
            {"field": "contract_status", "op": "eq", "value": "month_to_month"},
            {"field": "support_contacts_90d", "op": "gte", "value": 2},
        ]
    },
    "heavy-use upgrade": {
        "all": [
            {"field": "region", "op": "eq", "value": "north"},
            {"field": "internet_tier", "op": "in", "value": ["none", "basic"]},
            {"field": "data_gb_30d", "op": "gte", "value": 500},
        ]
    },
    "lapsed video offer": {
        "all": [
            {"field": "video_subscribed", "op": "eq", "value": True},
            {"field": "autopay", "op": "eq", "value": False},
            {"field": "days_since_last_offer", "op": "gte", "value": 180},
        ]
    },
}


def run_template(intent: str | None) -> Audience | None:
    predicate = INTENTS.get(intent) if intent else None
    if predicate is None:
        return None
    result = count_audience({"predicate": predicate})
    if result.count is None:
        return None
    return Audience.model_validate(
        {
            "predicates": predicate,
            "estimated_size": result.count,
            "status": "draft",
        }
    )
