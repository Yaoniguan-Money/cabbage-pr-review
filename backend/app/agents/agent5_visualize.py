from __future__ import annotations

import json

from app.agents.llm_helpers import call_flash_json
from app.local.diagram_meta import build_agent5_instruction, build_default_legend
from app.local.diagram_normalize import (
    build_global_compare_seed,
    collect_diagram_structural_notes,
    merge_degradation_notes,
    merge_diagram_seeds,
    normalize_diagrams,
)
from app.models.schemas import (
    DiagramLegendItem,
    DiffCompareSchema,
    DiffAtom,
    ProjectIndexSchema,
    ReviewStats,
    RiskReviewSchema,
    TaskResultSchema,
    VisualizationSchema,
)


def _atom_summary(atom: DiffAtom) -> dict:
    return {
        "id": atom.id,
        "file_path": atom.file_path,
        "change_type": atom.change_type,
        "symbol": atom.symbol,
        "summary": atom.summary,
    }


def run_agent5(
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    diff: DiffCompareSchema,
    review: RiskReviewSchema,
    pr_context: dict,
    project_type: str | None,
    framework: str | None,
    review_stats: ReviewStats | None = None,
) -> tuple[TaskResultSchema, list[str]]:
    payload = {
        "base_index": base.model_dump(),
        "head_index": head.model_dump(),
        "diff_atoms": [_atom_summary(a) for a in diff.all_atoms[:40]],
        "impact_diagram": diff.impact_diagram.model_dump() if diff.impact_diagram else None,
        "architecture_seed": base.architecture_diagram.model_dump() if base.architecture_diagram else None,
        "risks": [r.model_dump() for r in review.risks[:30]],
        "user_project_type": project_type,
        "user_framework": framework,
        "instruction": build_agent5_instruction(),
    }
    system = "你是 Agent5 可视化与结果组织 Agent（DeepSeek Flash）。"
    viz, notes = call_flash_json(system, json.dumps(payload, ensure_ascii=False), VisualizationSchema)

    if project_type:
        viz.detected_project_type = project_type
    if framework:
        viz.detected_framework = framework

    for diagram in viz.diagrams:
        if not diagram.legend:
            diagram.legend = [DiagramLegendItem(**item) for item in build_default_legend()]

    global_seed = build_global_compare_seed(base, head, diff)
    merged = merge_diagram_seeds(
        viz.diagrams,
        base.architecture_diagram,
        diff.impact_diagram,
        global_seed,
    )
    diagrams = normalize_diagrams(merged)
    diagram_notes = collect_diagram_structural_notes(diagrams)
    degradation_notes = merge_degradation_notes(
        review.degradation_notes,
        viz.structural_notes,
        diagram_notes,
    )

    return (
        TaskResultSchema(
            summary=viz.summary,
            summary_bullets=viz.summary_bullets,
            diagrams=diagrams,
            risks=review.risks,
            missing_info=review.missing_info,
            degradation_notes=degradation_notes,
            diff_atoms=diff.all_atoms,
            base_index=base,
            head_index=head,
            detected_project_type=viz.detected_project_type,
            detected_framework=viz.detected_framework,
            review_stats=review_stats,
        ),
        notes,
    )
