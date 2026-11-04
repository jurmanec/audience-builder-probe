# Audience Builder Probe

An objective becomes a checked audience: predicates, an estimated size, and a draft status. Nothing is sent to an outside platform.

Three paths share that audience shape and stop without writing a file when a check fails.

| Path     | What it does                                                                  |
| -------- | ----------------------------------------------------------------------------- |
| Template | Three known intents (audience labels), each a fixed predicate. No model call. |
| One shot | One model call and one count. No revision.                                    |
| Graph    | Plans a predicate, counts it, and may revise. Up to three attempts.           |

A count from 1 through 2,500 can become a draft audience. A count of 0, a count above 2,500, a rejected predicate, or a response that is not a predicate does not. The one-shot path stops after the first count. The graph may try again. The commands below write that draft. They do not approve it.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `XAI_API_KEY`. That file is not committed. The model is `grok-4.7`. A missing key makes no request.

Unit tests use scripted predicates and do not call the model. See [docs/how-to/run-tests.md](docs/how-to/run-tests.md).

## Run a template

Writes an audience file only for `at-risk renewal`, `heavy-use upgrade`, or `lapsed video offer`.

```sh
.venv/bin/python -m builder.template_runner "at-risk renewal" --out out/audience.json
```

## Run a one-shot

```sh
.venv/bin/python -m builder.oneshot_runner "Month-to-month households with at least a year of tenure and recent support contact." --out out/audience.json
```

## Run the graph

```sh
.venv/bin/python -m builder.graph_runner "Month-to-month households with at least a year of tenure and recent support contact." --out out/audience.json
```

## Score the three paths

Runs all eight objectives through each path and writes one score file. This command calls the model.

```sh
.venv/bin/python -m eval.score --out out/score.json
```

The notes from the recorded score are in [docs/decision-notes.md](docs/decision-notes.md).

## Tools

| Tool | What it does |
| --- | --- |
| `list_usable_attributes` | Reads the usable fields from the catalog. |
| `count_audience` | Checks a predicate, then counts matching rows. |

## Logs

Each tool call appends one JSON object to `logs/tool.jsonl`. The directory is gitignored. A line has `run_id`, `tool`, `arguments`, `outcome`, and `duration_ms`. A count also has `count`. A rejection also has `error_class`. `outcome` is `count`, `pass`, or `rejection`.

## A failed run

Exit `0` prints the path that was written. Exit `2` writes nothing. A miss does not delete an existing output file.

A failed run is an unknown template intent, a missing `XAI_API_KEY`, a predicate the catalog rejects, a count of 0 or above 2,500, or a model response that is not a predicate. No audience file is written.
