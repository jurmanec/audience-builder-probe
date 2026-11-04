# Decision notes

Written from `out/score.json` on 2026-11-03. The gold file and the graph were not changed to alter these results. The catalog stays the frozen slice of 11 usable attributes. This score separates the paths, so the catalog is not reopened.

A pass is a draft audience inside the size band, using only the objective's attribute families, or no file when the gold outcome is no audience. A template passes a known intent without a model call. The one-shot path makes one call. The graph may revise, up to three calls.

| Objective | Template | One shot | Graph |
| --- | --- | --- | --- |
| g01 at-risk renewal | pass | pass | pass |
| g02 heavy-use upgrade | pass | pass | pass |
| g03 lapsed video offer | pass | pass | pass |
| g04 in-term high bill, autopay off | missing audience | pass | pass |
| g05 south or west, three or more mobile lines | missing audience | pass | pass |
| g06 gig internet, first six months | missing audience | pass | pass |
| g07 targeted by age | pass | pass | pass |
| g08 tenure beyond 240 months | pass | pass | wrote an audience |

## Where a template remains the right tool

`g01`, `g02`, and `g03` are the three known intents. All three paths pass. The template does it with a fixed predicate and no model call. For a known intent, the template is the right tool.

`g08` asks for more tenure than the catalog allows. The gold outcome is no audience. The template writes nothing and passes. The one-shot path also writes nothing and passes. The graph wrote an audience and fails. On this objective the template is the right tool, and so is the one-shot path.

## Where the graph passes and the template does not

`g04`, `g05`, and `g06` have no template intent. The template writes nothing, so it fails. The graph and the one-shot path both pass. The graph earns a result there only in the sense that a fixed intent cannot cover an objective it was not given. The one-shot path reaches the same three passes with one call and no revision.

On this score the graph does not pass any objective that the one-shot path fails. The extra revision calls do not add a win. They are the path that failed `g08` by writing an audience the one-shot path refused.

## A second graph run of g07

In `out/score.json`, `g07` passes on all three paths. The gold outcome is no audience, and age is not a usable field. Writing nothing is the pass.

An earlier manual graph run, saved as `audience-g07.json`, wrote a different result for the same objective: tenure from 36 through 144 months, size 2300. That file would fail this score. It is a separate run, not the recorded score. The label stays no audience, and the graph is not changed to remove it.
