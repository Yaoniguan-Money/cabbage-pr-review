import json
from pathlib import Path

from app.local.quality_kpi import (
    QualityThresholds,
    compute_metrics,
    evaluate_metrics,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_compute_metrics_from_fixture_result_shape():
    viz = _load("visualization.json")
    risk = _load("risk_review.json")
    diff = _load("diff_compare.json")

    result = {
        "risks": risk.get("risks", []),
        "diagrams": viz.get("diagrams", []),
        "degradation_notes": [],
        "diff_atoms": diff.get("file_diffs", []),
        "missing_info": risk.get("missing_info", []),
    }
    metrics = compute_metrics(result)
    assert metrics.risks_count >= 1
    assert metrics.degradation_notes_count == 0
    assert metrics.diagrams_count >= 1


def test_evaluate_passes_with_default_thresholds():
    metrics = compute_metrics(
        {
            "risks": [{"id": "r1", "evidence": "patch line 10"}],
            "diagrams": [
                {"diagram_type": "architecture", "mermaid": "flowchart TB\n  A-->B"},
                {"diagram_type": "impact_overlay", "mermaid": "flowchart TB\n  A-->B"},
                {"diagram_type": "path_compare", "mermaid": "flowchart TB\n  A-->B"},
            ],
            "degradation_notes": [],
            "diff_atoms": [],
            "missing_info": [],
        }
    )
    ok, failures = evaluate_metrics(metrics, QualityThresholds(min_risks=1))
    assert ok is True
    assert failures == []


def test_evaluate_fails_when_degradation_exceeds_max():
    metrics = compute_metrics(
        {
            "risks": [],
            "diagrams": [],
            "degradation_notes": ["Agent4 校验失败"],
            "diff_atoms": [{"id": "a1"}],
            "missing_info": [],
        }
    )
    ok, failures = evaluate_metrics(
        metrics,
        QualityThresholds(max_degradation_notes=0, require_all_diagram_types=False),
    )
    assert ok is False
    assert any("degradation_notes_count" in f for f in failures)


def test_evaluate_fails_when_risks_empty_without_explanation():
    metrics = compute_metrics(
        {
            "risks": [],
            "diagrams": [],
            "degradation_notes": [],
            "diff_atoms": [{"id": "a1"}],
            "missing_info": [],
        }
    )
    ok, failures = evaluate_metrics(
        metrics,
        QualityThresholds(require_all_diagram_types=False),
    )
    assert ok is False
    assert any("diff_atoms" in f for f in failures)


def test_evidence_coverage_threshold():
    metrics = compute_metrics(
        {
            "risks": [
                {"id": "r1", "evidence": "ok"},
                {"id": "r2", "evidence": ""},
            ],
            "diagrams": [],
            "degradation_notes": [],
            "diff_atoms": [],
            "missing_info": [],
        }
    )
    assert metrics.risks_evidence_coverage == 0.5
    ok, failures = evaluate_metrics(
        metrics,
        QualityThresholds(
            require_all_diagram_types=False,
            min_risks_evidence_coverage=1.0,
        ),
    )
    assert ok is False
    assert any("risks_evidence_coverage" in f for f in failures)
