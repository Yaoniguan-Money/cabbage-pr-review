from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from app.agents.llm_helpers import LLMRequiredError
from app.graph.state import AgentOutcomeValue, GraphState
from app.models.schemas import ProjectIndexSchema


class EmptyAgentResultError(RuntimeError):
    """Raised when a critical agent returns an unusable empty result."""


def merge_notes(state: GraphState, notes: list[str]) -> list[str]:
    merged = list(state.get("degradation_notes", []))
    for note in notes:
        if note and note not in merged:
            merged.append(note)
    return merged


def empty_base() -> ProjectIndexSchema:
    return ProjectIndexSchema(version="base", raw_summary="")


def empty_head() -> ProjectIndexSchema:
    return ProjectIndexSchema(version="head", raw_summary="")


def agent_degradation_note(agent_id: int, exc: BaseException) -> str:
    return f"Agent{agent_id} degraded: {exc}"


def merge_agent_outcomes(
    state: GraphState,
    agent_id: int,
    outcome: AgentOutcomeValue,
) -> dict[int, AgentOutcomeValue]:
    outcomes = dict(state.get("agent_outcomes", {}))
    outcomes[agent_id] = outcome
    return outcomes


def merge_agent_errors(
    state: GraphState,
    agent_id: int,
    message: str,
) -> dict[int, str]:
    errors = dict(state.get("agent_errors", {}))
    if message.strip():
        errors[agent_id] = message.strip()
    return errors


def is_fatal_agent_error(exc: Exception) -> bool:
    if isinstance(exc, (LLMRequiredError, EmptyAgentResultError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}:
        return True
    msg = str(exc).lower()
    return any(token in msg for token in ("authentication", "unauthorized", "forbidden", "api key", "401", "403"))


def run_agent_safe(
    state: GraphState,
    agent_id: int,
    fn: Callable[[], dict[str, Any]],
    *,
    fallback: dict[str, Any],
    validator: Callable[[dict[str, Any]], None] | None = None,
    empty_is_fatal: bool = False,
) -> GraphState:
    try:
        payload = fn()
        if validator:
            validator(payload)
        payload["current_agent"] = agent_id
        payload["degradation_notes"] = merge_notes(state, list(payload.get("degradation_notes", [])))
        payload["agent_outcomes"] = merge_agent_outcomes(state, agent_id, "ok")
        return payload
    except EmptyAgentResultError as exc:
        prefix = "FAILED" if empty_is_fatal else "DEGRADED"
        outcome: AgentOutcomeValue = "failed" if empty_is_fatal else "degraded"
        note = f"{prefix}/Agent{agent_id}: {exc}"
        return {
            **fallback,
            "current_agent": agent_id,
            "agent_outcomes": merge_agent_outcomes(state, agent_id, outcome),
            "agent_errors": merge_agent_errors(state, agent_id, note),
            "degradation_notes": merge_notes(state, [note]),
        }
    except Exception as exc:
        fatal = is_fatal_agent_error(exc)
        prefix = "FAILED" if fatal else "DEGRADED"
        outcome: AgentOutcomeValue = "failed" if fatal else "degraded"
        note = f"{prefix}/Agent{agent_id}: {exc}"
        return {
            **fallback,
            "current_agent": agent_id,
            "agent_outcomes": merge_agent_outcomes(state, agent_id, outcome),
            "agent_errors": merge_agent_errors(state, agent_id, note),
            "degradation_notes": merge_notes(state, [note]),
        }
