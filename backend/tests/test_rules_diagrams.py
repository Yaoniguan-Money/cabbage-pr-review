"""规则模式四图生成测试。"""

from __future__ import annotations

import pytest

from app.local.demo_patches_meta import get_scenario_by_id, merge_demo_context_overlay
from app.local.file_io import parse_patch_text
from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_diagrams import build_rules_diagrams
from app.rules.pipeline.rules_index import run_rules_index
from app.rules.pipeline.rules_review import run_rules_review


def _demo_result(scenario_id: str):
    scenario = get_scenario_by_id(scenario_id)
    assert scenario is not None
    patches = parse_patch_text(scenario["patch_text"])
    ctx = merge_demo_context_overlay(
        {
            "patches": patches,
            "file_paths": [p["filename"] for p in patches],
        },
        scenario_id,
    )
    base, _ = run_rules_index(ctx, version="base")
    head, _ = run_rules_index(ctx, version="head")
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    diagrams = build_rules_diagrams(
        base_index=base,
        head_index=head,
        diff=diff,
        hits=hits,
        pr_context=ctx,
    )
    return diagrams, hits, scenario


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_scenarios_produce_four_diagrams(scenario_id: str):
    diagrams, _, _ = _demo_result(scenario_id)
    types = [d.diagram_type for d in diagrams]
    assert types == list(SCHEMA_DIAGRAM_TYPES)
    for diagram in diagrams:
        assert diagram.mermaid.strip()
        assert diagram.nodes


def test_s1_impact_marks_risk_on_changed_nodes():
    diagrams, hits, _ = _demo_result("S1-security")
    impact = next(d for d in diagrams if d.diagram_type == "impact_overlay")
    assert hits
    risky = [n for n in impact.nodes if n.risk is not None]
    assert risky


def test_s2_path_compare_has_before_after_groups():
    diagrams, _, _ = _demo_result("S2-change-surface")
    path_cmp = next(d for d in diagrams if d.diagram_type == "path_compare")
    groups = {n.group for n in path_cmp.nodes}
    assert "before" in groups
    assert "after" in groups


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_global_compare_from_architecture_seed(scenario_id: str):
    diagrams, _, _ = _demo_result(scenario_id)
    global_cmp = next(d for d in diagrams if d.diagram_type == "global_compare")
    groups = {n.group for n in global_cmp.nodes}
    assert "before" in groups
    assert "after" in groups
    assert len(global_cmp.edges) >= 3
