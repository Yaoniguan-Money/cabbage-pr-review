from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.agent1_base_scan import run_agent1
from app.agents.agent2_head_scan import run_agent2
from app.agents.agent3_diff import run_agent3
from app.agents.agent4_review import run_agent4
from app.agents.agent5_visualize import run_agent5
from app.graph.pipeline_dispatch import dispatch_node
from app.graph.state import GraphState
from app.graph.workflow_helpers import agent_degradation_note, empty_base, empty_head, merge_notes
from app.models.schemas import DiffCompareSchema, RiskReviewSchema, TaskResultSchema
from app.rules.workflow_nodes import (
    rules_node1,
    rules_node2,
    rules_node3,
    rules_node4,
    rules_node5,
)


def _llm_node1(state: GraphState) -> GraphState:
    try:
        base, notes = run_agent1(state["pr_context"])
        return {"base_index": base, "current_agent": 1, "degradation_notes": merge_notes(state, notes)}
    except Exception as e:
        return {
            "base_index": empty_base(),
            "current_agent": 1,
            "degradation_notes": merge_notes(state, [agent_degradation_note(1, e)]),
        }


def _llm_node2(state: GraphState) -> GraphState:
    try:
        head, notes = run_agent2(state["pr_context"])
        return {"head_index": head, "current_agent": 2, "degradation_notes": merge_notes(state, notes)}
    except Exception as e:
        return {
            "head_index": empty_head(),
            "current_agent": 2,
            "degradation_notes": merge_notes(state, [agent_degradation_note(2, e)]),
        }


def _llm_node3(state: GraphState) -> GraphState:
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()
    try:
        diff, notes = run_agent3(base, head, state["pr_context"])
        return {"diff_result": diff, "current_agent": 3, "degradation_notes": merge_notes(state, notes)}
    except Exception as e:
        return {
            "diff_result": DiffCompareSchema(),
            "current_agent": 3,
            "degradation_notes": merge_notes(state, [agent_degradation_note(3, e)]),
        }


def _llm_node4(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()
    rule_hits = list(state.get("rule_hits") or [])
    preflight_notes: list[str] = []
    try:
        if state.get("rules_preflight_enabled"):
            from app.rules.pipeline.rules_preflight import run_rules_preflight

            hits, preflight_notes = run_rules_preflight(
                diff,
                state["pr_context"],
                review_depth_mode=state.get("review_depth_mode") or "balanced",
            )
            rule_hits.extend(hits)
        review, notes, review_stats = run_agent4(
            diff,
            base,
            head,
            state["pr_context"],
            focus_atom_ids=state.get("focus_atom_ids"),
            extra_context_paths=state.get("extra_context_paths"),
            git_ws=state.get("git_ws"),
            review_depth_mode=state.get("review_depth_mode") or "balanced",
            rule_hits=rule_hits or None,
        )
        return {
            "review_result": review,
            "review_stats": review_stats,
            "rule_hits": rule_hits,
            "current_agent": 4,
            "degradation_notes": merge_notes(state, preflight_notes + notes),
        }
    except Exception as e:
        return {
            "review_result": RiskReviewSchema(degradation_notes=[str(e)]),
            "current_agent": 4,
            "degradation_notes": merge_notes(state, [agent_degradation_note(4, e)]),
        }


def _llm_node5(state: GraphState) -> GraphState:
    base = state.get("base_index") or empty_base()
    head = state.get("head_index") or empty_head()
    diff = state.get("diff_result") or DiffCompareSchema()
    review = state.get("review_result") or RiskReviewSchema()
    try:
        result, notes = run_agent5(
            base,
            head,
            diff,
            review,
            state["pr_context"],
            state.get("project_type"),
            state.get("framework"),
            review_stats=state.get("review_stats"),
            rule_hits=list(state.get("rule_hits") or []),
        )
        return {"final_result": result, "current_agent": 5, "degradation_notes": merge_notes(state, notes)}
    except Exception as e:
        return {
            "final_result": TaskResultSchema(summary="", degradation_notes=[str(e)]),
            "current_agent": 5,
            "degradation_notes": merge_notes(state, [agent_degradation_note(5, e)]),
        }


def _node1(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node1, _llm_node1)


def _node2(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node2, _llm_node2)


def _node3(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node3, _llm_node3)


def _node4(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node4, _llm_node4)


def _node5(state: GraphState) -> GraphState:
    return dispatch_node(state, rules_node5, _llm_node5)


def build_workflow():
    graph = StateGraph(GraphState)
    graph.add_node("agent1", _node1)
    graph.add_node("agent2", _node2)
    graph.add_node("agent3", _node3)
    graph.add_node("agent4", _node4)
    graph.add_node("agent5", _node5)
    graph.set_entry_point("agent1")
    graph.add_edge("agent1", "agent2")
    graph.add_edge("agent2", "agent3")
    graph.add_edge("agent3", "agent4")
    graph.add_edge("agent4", "agent5")
    graph.add_edge("agent5", END)
    return graph.compile()


workflow_app = build_workflow()

AGENT_NODE_ORDER = ["agent1", "agent2", "agent3", "agent4", "agent5"]
