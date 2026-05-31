"""Agent1/Agent2 并行扫描节点实现。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.graph.scan_nodes import llm_node1, llm_node2
from app.graph.state import GraphState
from app.graph.workflow_helpers import merge_notes
from app.local.llm_mode import is_rules_only_mode
from app.rules.workflow_nodes import rules_node1, rules_node2
from app.services import task_progress


def _run_scan_branch(state: GraphState, agent_id: int) -> tuple[int, dict[str, Any]]:
    if agent_id == 1:
        update = rules_node1(state) if is_rules_only_mode(state.get("llm_mode")) else llm_node1(state)
    elif agent_id == 2:
        update = rules_node2(state) if is_rules_only_mode(state.get("llm_mode")) else llm_node2(state)
    else:
        raise ValueError(f"无效的并行扫描 agent_id: {agent_id}")
    return agent_id, update


def _merge_branch_update(merged: dict[str, Any], update: dict[str, Any]) -> None:
    if update.get("base_index") is not None:
        merged["base_index"] = update["base_index"]
    if update.get("head_index") is not None:
        merged["head_index"] = update["head_index"]
    if update.get("degradation_notes"):
        merged["degradation_notes"] = merge_notes(
            {"degradation_notes": merged["degradation_notes"]},
            update["degradation_notes"],
        )
    if update.get("agent_outcomes"):
        outcomes = dict(merged.get("agent_outcomes") or {})
        outcomes.update(update["agent_outcomes"])
        merged["agent_outcomes"] = outcomes
    if update.get("agent_errors"):
        errors = dict(merged.get("agent_errors") or {})
        errors.update(update["agent_errors"])
        merged["agent_errors"] = errors


def run_parallel_scan(state: GraphState) -> GraphState:
    task_progress.set_agent_status(1, "running")
    task_progress.set_agent_status(2, "running")

    merged: dict[str, Any] = {
        "degradation_notes": list(state.get("degradation_notes") or []),
        "agent_outcomes": dict(state.get("agent_outcomes") or {}),
        "agent_errors": dict(state.get("agent_errors") or {}),
    }
    errors: dict[int, str] = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_run_scan_branch, state, agent_id): agent_id for agent_id in (1, 2)
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            try:
                aid, update = future.result()
                _merge_branch_update(merged, update)
                outcome = (update.get("agent_outcomes") or {}).get(aid, "ok")
                if outcome == "failed":
                    task_progress.set_agent_status(aid, "failed", (update.get("agent_errors") or {}).get(aid, ""))
                elif outcome == "degraded":
                    task_progress.set_agent_status(aid, "degraded", (update.get("agent_errors") or {}).get(aid, ""))
                else:
                    task_progress.set_agent_status(aid, "completed")
            except Exception as exc:
                errors[agent_id] = str(exc)
                task_progress.set_agent_status(agent_id, "failed", str(exc))

    if errors:
        raise RuntimeError("; ".join(f"Agent{aid}: {msg}" for aid, msg in sorted(errors.items())))

    merged["current_agent"] = 2
    return merged  # type: ignore[return-value]
