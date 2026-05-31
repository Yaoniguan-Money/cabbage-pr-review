from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.models.schemas import DiffCompareSchema, ProjectIndexSchema, RiskReviewSchema, TaskResultSchema

AgentOutcomeValue = Literal["ok", "degraded", "failed"]


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
    agent_outcomes: dict[int, AgentOutcomeValue]
    agent_errors: dict[int, str]
    current_agent: int
