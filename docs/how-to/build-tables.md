# Build tables from json fixtures

## Env and dependencies
```sh
source .venv/bin/activate
pip install -r requirements.txt 
```

## Catolog
```sh   
.venv/bin/python corpus/load_catalog.py
```

## Households
```sh
.venv/bin/python -m corpus.load_households
```

