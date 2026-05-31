from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.agent3_diff import run_agent3
from app.agents.agent4_review import run_agent4
from app.agents.agent5_visualize import run_agent5
from app.graph.parallel_scan import run_parallel_scan
from app.graph.pipeline_dispatch import dispatch_node
from app.graph.state import GraphState
from app.graph.workflow_helpers import EmptyAgentResultError, empty_base, empty_head, run_agent_safe
from app.local.workflow_meta import AGENT_NODE_ORDER
from app.models.schemas import DiffCompareSchema, RiskReviewSchema, TaskResultSchema
from app.rules.workflow_nodes import rules_node3, rules_node4, rules_node5


def _scan_parallel_node(state: GraphState) -> GraphState:
    return run_parallel_scan(state)


def _llm_node3(state: GraphState) -> GraphState:
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()

    def _run() -> GraphState:
        diff, notes = run_agent3(base, head, state["pr_context"])
        return {
            "diff_result": diff,
            "degradation_notes": notes,
        }

    def _validate(payload: GraphState) -> None:
        diff = payload.get("diff_result")
        if not diff or not diff.all_atoms:
            raise EmptyAgentResultError("diff_result has no atoms")

    return run_agent_safe(
        state,
        3,
        _run,
        fallback={"diff_result": DiffCompareSchema()},
        validator=_validate,
        empty_is_fatal=True,
    )


def _llm_node4(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()

    def _run() -> GraphState:
        review, notes, review_stats = run_agent4(
            diff,
            base,
            head,
            state["pr_context"],
            focus_atom_ids=state.get("focus_atom_ids"),
            extra_context_paths=state.get("extra_context_paths"),
            git_ws=state.get("git_ws"),
            review_depth_mode=state.get("review_depth_mode") or "balanced",
        )
        return {
            "review_result": review,
            "review_stats": review_stats,
            "degradation_notes": notes,
        }

    def _validate(payload: GraphState) -> None:
        review = payload.get("review_result")
        if not review:
            raise EmptyAgentResultError("review_result is missing")
        if not review.risks and not review.missing_info and not review.degradation_notes:
            raise EmptyAgentResultError("review_result has no risks, missing_info, or degradation_notes")

    return run_agent_safe(
        state,
        4,
        _run,
        fallback={"review_result": RiskReviewSchema()},
        validator=_validate,
        empty_is_fatal=True,
    )


def _llm_node5(state: GraphState) -> GraphState:
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()
    diff = state.get("diff_result") or DiffCompareSchema()
    review = state.get("review_result") or RiskReviewSchema()

    def _run() -> GraphState:
        result, notes = run_agent5(
            base,
            head,
            diff,
            review,
            state["pr_context"],
            state.get("project_type"),
            state.get("framework"),
            review_stats=state.get("review_stats"),
        )
        return {
            "final_result": result,
            "degradation_notes": notes,
        }

    def _validate(payload: GraphState) -> None:
        result = payload.get("final_result")
        if not result or not result.summary.strip():
            raise EmptyAgentResultError("final_result.summary is empty")

    return run_agent_safe(
        state,
        5,
        _run,
        fallback={"final_result": TaskResultSchema()},
        validator=_validate,
        empty_is_fatal=True,
    )


def _node3(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node3, _llm_node3)


def _node4(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node4, _llm_node4)


def _node5(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node5, _llm_node5)


def build_workflow():
    graph = StateGraph(GraphState)
    graph.add_node("scan_parallel", _scan_parallel_node)
    graph.add_node("agent3", _node3)
    graph.add_node("agent4", _node4)
    graph.add_node("agent5", _node5)
    graph.set_entry_point("scan_parallel")
    graph.add_edge("scan_parallel", "agent3")
    graph.add_edge("agent3", "agent4")
    graph.add_edge("agent4", "agent5")
    graph.add_edge("agent5", END)
    return graph.compile()


workflow_app = build_workflow()

__all__ = ["workflow_app", "AGENT_NODE_ORDER"]
