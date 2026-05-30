"""Workflow 节点共享 helper（LLM / 规则双 pipeline 共用）。"""

from __future__ import annotations

from app.graph.state import GraphState
from app.models.schemas import ProjectIndexSchema


def merge_notes(state: GraphState, notes: list[str]) -> list[str]:
    all_notes = list(state.get("degradation_notes", []))
    all_notes.extend(notes)
    return all_notes


def empty_base() -> ProjectIndexSchema:
    return ProjectIndexSchema(version="base", raw_summary="")


def empty_head() -> ProjectIndexSchema:
    return ProjectIndexSchema(version="head", raw_summary="")


def agent_degradation_note(agent_id: int, exc: BaseException) -> str:
    return f"Agent{agent_id} 局部降级: {exc}"
