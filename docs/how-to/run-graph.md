# Run the graph

Writes an audience file only when the plan-and-revise loop returns a draft audience. A miss writes no audience file and no brief file. The command does not approve an audience.

```sh
.venv/bin/python -m builder.graph_runner "Month-to-month households with at least a year of tenure and recent support contact." --out out/audience.json
```

Exit `0` prints the audience path. Exit `2` means nothing was written. The default model is `grok-4.7`. Put the key in `.env` in the project root as `XAI_API_KEY=...`. That file is not committed. A missing key makes no request and exits `2`.

Tool calls are appended to `logs/tool.jsonl`.
