# Marketing Domain and Process — Template Intent and Predicates

In marketing operations, a recurring objective is often handled with a pre-defined approach rather than rebuilt from scratch every time.

- A **template intent** is a known, repeatable campaign type (for example “win-back,” “fiber upgrade,” or “contract renewal”). The organization already understands the usual audience logic for that intent.
- A **predicate** is the concrete rule that selects the audience for that intent (for example `tenure >= 24 AND current_product != "fiber" AND region = "Northeast"`). It is the condition that gets applied to the customer/household data to produce a countable segment.

Marketers and campaign systems use these pre-built predicates when the objective matches a familiar pattern. The predicates are executed against the household table to estimate size and, if approved, to export the audience. This path is fast, cheap, and consistent for objectives the team already knows well.
