#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[lint] ruff"
python -m ruff check src tests

echo "[lint] mypy"
python -m mypy src/app

echo "[lint] pytest collect-only"
python -m pytest tests/ --collect-only -q

# lint-anchor-01
# lint-anchor-02
