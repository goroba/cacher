# cacher

A Python library.

## Install

```bash
pip install cacher
pip install "cacher[redis]"
pip install "cacher[pydantic]"
pip install "cacher[redis,pydantic]"
```

From a checkout, the same extras are:

```bash
pip install -e ".[dev]"
pip install -e ".[redis]"
pip install -e ".[redis,pydantic]"
```

Runtime dependencies live in `pyproject.toml` under `[project] dependencies`. Optional Redis and Pydantic support, and the test tools, live in extras. A plain install does not pull Redis or Pydantic. There is no `requirements.txt`.

## Test

```bash
pytest
```

## Publish

When the package is ready for PyPI, build and upload it. Confirm the project name is free on PyPI first, and fill in the author details in `pyproject.toml`.

```bash
pip install build twine
python -m build
twine upload dist/*
```
