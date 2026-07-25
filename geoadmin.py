name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: pip install -e ".[dev]"
      - name: Lint
        run: python -m ruff check src tests
      - name: Test (excluding live)
        run: PYTHONPATH=src pytest tests/ -m "not live"

  publish:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: test
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Build
        run: pip install build && python -m build
      - name: Publish to PyPI (OIDC Trusted Publisher)
        uses: pypa/gh-action-pypi-publish@release/v1
