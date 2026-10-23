#!/usr/bin/env bash
# Lint, format check, and unit tests with coverage. Add RUN_INTEGRATION=1 to also hit Supabase.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-.venv/bin/python}

$PY -m ruff check .
$PY -m ruff format --check .
$PY -m pytest --cov=app --cov-report=term-missing --cov-fail-under=90 "$@"
