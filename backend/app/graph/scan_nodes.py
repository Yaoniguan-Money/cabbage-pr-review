"""Agent1/2 单路扫描节点（供并行扫描与工作流复用）。"""

from __future__ import annotations

from app.agents.agent1_base_scan import run_agent1
from app.agents.agent2_head_scan import run_agent2
from app.graph.state import GraphState
from app.graph.workflow_helpers import empty_base, empty_head, run_agent_safe


def llm_node1(state: GraphState) -> GraphState:
    def _run() -> GraphState:
        base, notes = run_agent1(state["pr_context"])
        return {
            "base_index": base,
            "degradation_notes": notes,
        }

    return run_agent_safe(state, 1, _run, fallback={"base_index": empty_base()})


def llm_node2(state: GraphState) -> GraphState:
    def _run() -> GraphState:
        head, notes = run_agent2(state["pr_context"])
        return {
            "head_index": head,
            "degradation_notes": notes,
        }

    return run_agent_safe(state, 2, _run, fallback={"head_index": empty_head()})
