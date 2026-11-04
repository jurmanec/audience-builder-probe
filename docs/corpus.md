## At risk predicate on households
2147 rows returned.

## Heavy use upgrade predicate on households 
440

## Lapsed video offer predicate on households
1052

## Gold set
Eval only: [eval/gold.json](../eval/gold.json). The catalog and household loaders do not read this file.

## Campaign library
[corpus/campaigns.json](../corpus/campaigns.json). A brief copies the approved audience plus the offer, channels, and constraint from one campaign. No selected campaign means no brief.

## M0 freeze
Frozen 2026-11-02. Gold-set size was reopened the same day from 6 to 8 to add two fail-closed objectives. These values stay as written unless M0 is explicitly reopened.

| Item | Value |
|---|---|
| Households | 5,000 rows, seed `20261102`, in [corpus/households.json](../corpus/households.json) |
| Catalog | 11 usable attributes, 3 forbidden, in [corpus/catalog.json](../corpus/catalog.json) |
| Gold set | 8 objectives, [eval/gold.json](../eval/gold.json). `g07` and `g08` expect no audience. |
| Campaign library | 4 campaigns, [corpus/campaigns.json](../corpus/campaigns.json) |
| Template intents | at-risk renewal, heavy-use upgrade, lapsed video offer |
| Database | DuckDB, file `corpus/intake.duckdb` |
| Audience fields | `predicates`, `estimated_size`, `status` |
| Brief fields | approved audience, campaign id, offer, channels, constraint |
| Default model provider | xAI, model `grok-4.7`, behind a thin interface. Bedrock stays an optional later swap. |

The 5,000 rows draw each attribute independently, so the counts are not joint patterns of real households.