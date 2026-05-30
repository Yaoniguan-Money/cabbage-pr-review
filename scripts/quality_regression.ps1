param(
    [Parameter(Mandatory = $true)]
    [string]$PrUrl,
    [string]$ApiBase = "http://localhost:8000",
    [ValidateSet("cloud_only", "hybrid", "local_only", "")]
    [string]$LlmMode = "",
    [Nullable[bool]]$LocalCompress = $null,
    [int]$MinRisks = 1,
    [int]$MaxDegradationNotes = 0,
    [bool]$RequireAllDiagramTypes = $true,
    [double]$MinRisksEvidenceCoverage = 0.0,
    [int]$TimeoutMinutes = 12
)

$ErrorActionPreference = "Stop"

function Get-ThresholdsFromJson {
    param([string]$Path)
    $raw = Get-Content -Raw -Path $Path | ConvertFrom-Json
    return @{
        MinRisks                     = [int]$raw.min_risks
        MaxDegradationNotes          = [int]$raw.max_degradation_notes
        RequireAllDiagramTypes       = [bool]$raw.require_all_diagram_types
        MinRisksEvidenceCoverage     = [double]$raw.min_risks_evidence_coverage
        RequireMissingInfoWhenNoRisks = [bool]$raw.require_missing_info_when_no_risks
    }
}

if ($env:QUALITY_THRESHOLDS_JSON) {
    $fromFile = Get-ThresholdsFromJson -Path $env:QUALITY_THRESHOLDS_JSON
    if ($PSBoundParameters.ContainsKey("MinRisks") -eq $false) { $MinRisks = $fromFile.MinRisks }
    if ($PSBoundParameters.ContainsKey("MaxDegradationNotes") -eq $false) {
        $MaxDegradationNotes = $fromFile.MaxDegradationNotes
    }
    if ($PSBoundParameters.ContainsKey("RequireAllDiagramTypes") -eq $false) {
        $RequireAllDiagramTypes = $fromFile.RequireAllDiagramTypes
    }
    if ($PSBoundParameters.ContainsKey("MinRisksEvidenceCoverage") -eq $false) {
        $MinRisksEvidenceCoverage = $fromFile.MinRisksEvidenceCoverage
    }
}

Write-Output "PR_URL=$PrUrl"
Write-Output "API_BASE=$ApiBase"
Write-Output "THRESHOLDS min_risks=$MinRisks max_degradation_notes=$MaxDegradationNotes"
if ($LlmMode) { Write-Output "LLM_MODE=$LlmMode" }
if ($null -ne $LocalCompress) { Write-Output "LOCAL_COMPRESS=$LocalCompress" }

$body = @{ input_type = "pr_url"; value = $PrUrl }
if ($LlmMode) { $body["llm_mode"] = $LlmMode }
if ($null -ne $LocalCompress) { $body["local_compress_enabled"] = $LocalCompress }
$body = $body | ConvertTo-Json
$task = Invoke-RestMethod -Uri "$ApiBase/api/tasks" -Method Post -ContentType "application/json" -Body $body
$taskId = $task.id
Write-Output "TASK_ID=$taskId"

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
do {
    Start-Sleep -Seconds 4
    $t = Invoke-RestMethod -Uri "$ApiBase/api/tasks/$taskId"
    Write-Output ("STATUS=" + $t.status + " AGENT=" + $t.current_agent)
} while ($t.status -in @("pending", "running") -and (Get-Date) -lt $deadline)

if ($t.status -ne "completed") {
    Write-Error ("任务未完成: status=" + $t.status + " error=" + $t.error_message)
    exit 1
}

$result = Invoke-RestMethod -Uri "$ApiBase/api/tasks/$taskId/result"

$repoRoot = Split-Path -Parent $PSScriptRoot
$evalScript = @"
import json, sys
sys.path.insert(0, r"$repoRoot\backend")
from app.local.quality_kpi import QualityThresholds, compute_metrics, evaluate_metrics
result = json.loads(sys.stdin.read())
metrics = compute_metrics(result)
thresholds = QualityThresholds(
    min_risks=$MinRisks,
    max_degradation_notes=$MaxDegradationNotes,
    require_all_diagram_types=$($RequireAllDiagramTypes.ToString().ToLower()),
    min_risks_evidence_coverage=$MinRisksEvidenceCoverage,
)
ok, failures = evaluate_metrics(metrics, thresholds)
print(json.dumps({"ok": ok, "metrics": metrics.to_dict(), "failures": failures}, ensure_ascii=False))
sys.exit(0 if ok else 1)
"@

$evalJson = ($result | ConvertTo-Json -Depth 20 -Compress) | python -c $evalScript
$eval = $evalJson | ConvertFrom-Json

Write-Output ("RISKS=" + $eval.metrics.risks_count)
Write-Output ("DEGRADE_NOTES=" + $eval.metrics.degradation_notes_count)
Write-Output ("DIAGRAMS=" + $eval.metrics.diagrams_count)
Write-Output ("EVIDENCE_COVERAGE=" + $eval.metrics.risks_evidence_coverage)

foreach ($dtype in @("architecture", "impact_overlay", "path_compare")) {
    $has = $eval.metrics.diagram_has_mermaid.$dtype
    Write-Output ("DIAGRAM_" + $dtype.ToUpper() + "_MERMAID=" + $has)
}

if (-not $eval.ok) {
    Write-Output "KPI_FAILED=true"
    foreach ($f in $eval.failures) { Write-Output ("FAILURE=" + $f) }
    exit 1
}

Write-Output "KPI_PASSED=true"
exit 0
