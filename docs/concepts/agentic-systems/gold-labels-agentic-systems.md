# Gold Labels in Agentic Systems

**Gold labels** (also called golden examples, gold sets, or reference cases) are curated input–output pairs used to evaluate agentic systems.

In agentic systems, a gold label typically consists of:

- An input (a user goal, query, or task description)
- An expected outcome expressed as constraints or an acceptable result, rather than one exact trace

Because agents can take multiple valid paths (different tool sequences, different intermediate steps), gold labels usually define success criteria—such as required final fields, prohibited actions, acceptable ranges, or must-include facts—instead of mandating a single correct sequence of steps.

They are used to:

- Measure whether an agent accomplishes the task
- Compare different agent designs, prompts, or models on the same cases
- Detect regressions when the system changes
- Provide a stable, repeatable signal that does not rely solely on human review or LLM-as-judge scoring

A well-constructed gold set is one of the primary ways teams evaluate and improve agent reliability.
