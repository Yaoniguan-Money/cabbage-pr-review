from __future__ import annotations

from typing import Any, TypedDict

from app.models.schemas import DiffCompareSchema, ProjectIndexSchema, ReviewStats, RiskReviewSchema, TaskResultSchema
from app.rules.rule_schema import RuleHitRecord


class GraphState(TypedDict, total=False):
    pr_context: dict[str, Any]
    git_ws: Any
    project_type: str | None
    framework: str | None
    focus_atom_ids: list[str]
    extra_context_paths: list[str]
    base_index: ProjectIndexSchema | None
    head_index: ProjectIndexSchema | None
    diff_result: DiffCompareSchema | None
    review_result: RiskReviewSchema | None
    final_result: TaskResultSchema | None
    degradation_notes: list[str]
    current_agent: int
    review_depth_mode: str | None
    review_stats: ReviewStats | None
    llm_mode: str
    rule_hits: list[RuleHitRecord]
    rules_preflight_enabled: bool
