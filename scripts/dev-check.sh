#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q app.py src
python -m pytest -q
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests app.py
else
  echo 'ruff not installed in this environment; CI will run the lint gate.'
fi
python -m menushift.cli --dish suya --budget 1500 --protein 10 --sensitivity >/dev/null
