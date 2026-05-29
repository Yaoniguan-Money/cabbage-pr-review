from __future__ import annotations

import json

from app.agents.llm_helpers import call_flash_json
from app.local.diagram_utils import attach_mermaid_list
from app.models.schemas import (
    DiffCompareSchema,
    ProjectIndexSchema,
    ReviewStats,
    RiskReviewSchema,
    TaskResultSchema,
    VisualizationSchema,
)


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
        "diff_summary": {"atoms": len(diff.all_atoms)},
        "risks": [r.model_dump() for r in review.risks[:30]],
        "user_project_type": project_type,
        "user_framework": framework,
        "instruction": (
            "输出 VisualizationSchema：summary、summary_bullets、detected_project_type、detected_framework，"
            "以及 diagrams 恰好 3 张：architecture、impact_overlay、path_compare。"
            "每张图必须含 nodes/edges，每个节点尽量含 confidence 与 risk（如适用）。不要输出 mermaid。"
        ),
    }
    system = "你是 Agent5 可视化与结果组织 Agent（DeepSeek Flash）。"
    viz, notes = call_flash_json(system, json.dumps(payload, ensure_ascii=False), VisualizationSchema)

    if project_type:
        viz.detected_project_type = project_type
    if framework:
        viz.detected_framework = framework

    diagrams = attach_mermaid_list(viz.diagrams)
    if base.architecture_diagram and not any(d.diagram_type == "architecture" for d in diagrams):
        diagrams.insert(0, attach_mermaid(base.architecture_diagram) or base.architecture_diagram)
    if diff.impact_diagram and not any(d.diagram_type == "impact_overlay" for d in diagrams):
        diagrams.append(attach_mermaid(diff.impact_diagram) or diff.impact_diagram)

    return (
        TaskResultSchema(
            summary=viz.summary,
            summary_bullets=viz.summary_bullets,
            diagrams=diagrams,
            risks=review.risks,
            missing_info=review.missing_info,
            degradation_notes=review.degradation_notes,
            diff_atoms=diff.all_atoms,
            base_index=base,
            head_index=head,
            detected_project_type=viz.detected_project_type,
            detected_framework=viz.detected_framework,
            review_stats=review_stats,
        ),
        notes,
    )
