# Score the three paths

Writes one score file for the template path, the one-shot path, and the graph on all eight gold objectives. A missing `XAI_API_KEY` makes no request and writes no score file.

```sh
.venv/bin/python -m eval.score --out out/score.json
```

Exit `0` prints the score path. Exit `2` means nothing was written. The one-shot path makes one model call per objective. The graph makes up to three. The score does not call a judge model and does not change `eval/gold.json`.

Unit tests inject scripted predicates and do not call the model. See [run the unit tests](run-tests.md).
