param(
    [switch]$IncludeLive,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python scripts/build_pr_review_evidence_dataset.py
$env:PYTHONPATH = Join-Path $Root "backend"

if ($IncludeLive) {
    if ([string]::IsNullOrWhiteSpace($env:DASHSCOPE_API_KEY)) {
        throw "DASHSCOPE_API_KEY is required for -IncludeLive"
    }
    python scripts/run_pr_review_evidence.py --live
} else {
    python scripts/run_pr_review_evidence.py
}

Push-Location backend
try {
    python -m pytest tests --junitxml=../evidence/raw/backend-pytest.xml --cov=app --cov-branch --cov-report=json:../evidence/raw/backend-coverage.json
} finally {
    Pop-Location
}

Push-Location frontend
try {
    if (-not $SkipInstall) {
        npm ci
    }
    npm test -- --run --reporter=json --outputFile=../evidence/raw/frontend-vitest.json
    npm run build
} finally {
    Pop-Location
}

python scripts/capture_evidence_environment.py
if ($IncludeLive) {
    python scripts/validate_pr_review_evidence.py --require-live
} else {
    python scripts/validate_pr_review_evidence.py
}
