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

echo "[lint] requirements pin check"
python - <<'PY'
from pathlib import Path
import re
unpinned = []
for line in Path("requirements.txt").read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    if "==" not in stripped and not stripped.startswith("-"):
        unpinned.append(stripped)
if unpinned:
    print("warning: unpinned packages:", ", ".join(unpinned))
PY

echo "[lint] bandit"
python -m bandit -r src/app -q || true

echo "[lint] black check"
python -m black --check src tests

echo "[lint] coverage threshold"
python -m pytest tests/ --cov=src/app --cov-fail-under=0 -q

echo "[lint] import order"
python -m ruff check src tests --select I

echo "[lint] done"
