# Run the unit tests

Run these from the project root. They use scripted predicates and do not call the model.

One module:

```sh
.venv/bin/python -m unittest tests.test_oneshot
```

A module under `corpus/` uses its package name:

```sh
.venv/bin/python -m unittest corpus.test_gold
```

Every test module:

```sh
.venv/bin/python -m unittest discover
```
