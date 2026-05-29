from __future__ import annotations

from typing import Any, TypedDict

from app.models.schemas import DiffCompareSchema, ProjectIndexSchema, RiskReviewSchema, TaskResultSchema


class GraphState(TypedDict, total=False):
    pr_context: dict[str, Any]
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
