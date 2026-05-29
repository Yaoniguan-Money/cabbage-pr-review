from app.local.result_repair import repair_model
from app.models.schemas import AtomContextPlanBatch, RiskReviewSchema, VisualizationSchema


def test_repair_atom_plan_batch_converts_new_concerns_to_list():
    raw = {
        "plans": [
            {
                "atom_id": "a1",
                "diff_type": "route",
                "layer1_paths": ["a.py"],
                "layer2_paths": [],
                "need_deeper": True,
                "new_concerns": "single concern text",
            }
        ]
    }
    fixed = repair_model(AtomContextPlanBatch, raw)
    assert isinstance(fixed.plans[0].new_concerns, list)
    assert fixed.plans[0].new_concerns == ["single concern text"]


def test_repair_risk_review_fills_required_fields_without_hardcode():
    raw = {
        "risks": [
            {
                "atom_id": "a1",
                "evidence": "README changed",
                "suggestion": "add test",
            }
        ]
    }
    fixed = repair_model(RiskReviewSchema, raw)
    assert len(fixed.risks) == 1
    assert fixed.risks[0].id
    assert fixed.risks[0].title
    assert fixed.risks[0].description
    assert fixed.risks[0].related_atoms == ["a1"]
    assert any("自动修复风险结构" in note for note in fixed.degradation_notes)


def test_repair_visualization_maps_from_to_and_numeric_confidence():
    raw = {
        "summary": "ok",
        "summary_bullets": ["a"],
        "diagrams": [
            {
                "diagram_type": "architecture",
                "nodes": [{"id": "n1", "label": "node", "confidence": 0.9}],
                "edges": [{"from": "n1", "to": "n1", "label": "self"}],
            }
        ],
    }
    fixed = repair_model(VisualizationSchema, raw)
    assert fixed.diagrams[0].nodes[0].confidence.value == "high"
    assert fixed.diagrams[0].edges[0].source == "n1"
    assert fixed.diagrams[0].edges[0].target == "n1"
