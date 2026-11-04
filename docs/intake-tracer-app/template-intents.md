# Template intents

`templates.py` is a tiny saved-segment library. A large telecommunications marketing platform already has that library. It is a catalog of named audiences, not a list of English sentences.

`INTENTS` maps three names to fixed predicates. `run_template` looks up the name, counts the stored rule, and returns a draft audience with that predicate and the current size. An unknown name returns nothing.

```python
INTENTS: dict[str, dict] = {
    "at-risk renewal": {
        "all": [
            {"field": "tenure_months", "op": "gte", "value": 12},
            {"field": "contract_status", "op": "eq", "value": "month_to_month"},
            {"field": "support_contacts_90d", "op": "gte", "value": 2},
        ]
    },
}
```

Opening a published segment works the same way. The rule is already built, the platform refreshes the count, and the segment is not yet approved for this campaign.

In the real platform the dictionary key is a segment id. The thing a marketer sees is a name in a folder, such as "Month-to-month at risk," "Heavy-use internet upgrade," or "Lapsed video, autopay off." Each record stores the segment-builder rule, an owner, a certification status, and often suppressions and a refresh schedule. Lifecycle and audience-operations teams publish the canonical ones. Campaign managers search or clone them. They do not type a one-line intent that must match exactly. `"at-risk renewal"` is this project's stand-in for that saved name.

The library covers the motions the company runs all the time: renewal, upgrade, win-back, onboarding, save. There are hundreds of saved segments, many of them regional or product variants of a smaller set of patterns. A campaign template one level up often points at one of those segments and also fills the offer, channel, and suppression. This code stops at the audience draft.

What the library does not contain is a new ask. "In-term, high bill, autopay off" has no saved segment until someone builds it. That person opens the segment builder, picks attributes from the catalog, and saves a new rule. In this project that is the one-shot path and the graph. The template path fails those objectives because the name is not in `INTENTS`. Marketers have a dictionary of known audiences. They do not have a dictionary of every sentence someone might type.

## Segment builder rule

A segment builder rule is the stored definition of who is in the audience. In this project that definition is the predicate.

The names come from two sides of the same object. "Predicate" is the word this repo uses for the JSON: one `all` list of `field`, `op`, and `value`. "Segment builder rule" is the word a marketing platform uses for the same kind of definition as a marketer sees it in the audience tool. When `templates.py` maps `"at-risk renewal"` to a predicate, that predicate is the saved segment's rule.

A production rule is usually a larger version of the same idea. It can include OR groups, exclusions, another saved segment, and a time window. This project's predicate cannot. It is AND-only, with no nesting. The terms name the same role, and this predicate is a deliberately small rule.
