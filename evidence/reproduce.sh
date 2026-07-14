#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
INCLUDE_LIVE=0
SKIP_INSTALL=0
for arg in "$@"; do
  case "$arg" in
    --include-live) INCLUDE_LIVE=1 ;;
    --skip-install) SKIP_INSTALL=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

python scripts/build_pr_review_evidence_dataset.py
export PYTHONPATH="$ROOT/backend"
if [[ "$INCLUDE_LIVE" -eq 1 ]]; then
  : "${DASHSCOPE_API_KEY:?DASHSCOPE_API_KEY is required for --include-live}"
  python scripts/run_pr_review_evidence.py --live
else
  python scripts/run_pr_review_evidence.py
fi

(
  cd backend
  python -m pytest tests --junitxml=../evidence/raw/backend-pytest.xml --cov=app --cov-branch --cov-report=json:../evidence/raw/backend-coverage.json
)
(
  cd frontend
  if [[ "$SKIP_INSTALL" -eq 0 ]]; then npm ci; fi
  npm test -- --run --reporter=json --outputFile=../evidence/raw/frontend-vitest.json
  npm run build
)
python scripts/capture_evidence_environment.py
if [[ "$INCLUDE_LIVE" -eq 1 ]]; then
  python scripts/validate_pr_review_evidence.py --require-live
else
  python scripts/validate_pr_review_evidence.py
fi
