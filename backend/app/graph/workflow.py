from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.agent1_base_scan import run_agent1
from app.agents.agent2_head_scan import run_agent2
from app.agents.agent3_diff import run_agent3
from app.agents.agent4_review import run_agent4
from app.agents.agent5_visualize import run_agent5
from app.graph.state import GraphState


def _node1(state: GraphState) -> GraphState:
    try:
        base = run_agent1(state["pr_context"])
        return {"base_index": base, "current_agent": 1, "degradation_notes": state.get("degradation_notes", [])}
    except Exception as e:
        notes = list(state.get("degradation_notes", []))
        notes.append(f"Agent1 局部降级: {e}")
        from app.models.schemas import ProjectIndexSchema

        return {"base_index": ProjectIndexSchema(raw_summary="降级"), "current_agent": 1, "degradation_notes": notes}


def _node2(state: GraphState) -> GraphState:
    try:
        head = run_agent2(state["pr_context"])
        return {"head_index": head, "current_agent": 2}
    except Exception as e:
        notes = list(state.get("degradation_notes", []))
        notes.append(f"Agent2 局部降级: {e}")
        from app.models.schemas import ProjectIndexSchema

        return {"head_index": ProjectIndexSchema(), "current_agent": 2, "degradation_notes": notes}


def _node3(state: GraphState) -> GraphState:
    base = state.get("base_index")
    head = state.get("head_index")
    if not base or not head:
        from app.models.schemas import DiffCompareSchema

        return {"diff_result": DiffCompareSchema(), "current_agent": 3}
    try:
        diff = run_agent3(base, head, state["pr_context"])
        return {"diff_result": diff, "current_agent": 3}
    except Exception as e:
        notes = list(state.get("degradation_notes", []))
        notes.append(f"Agent3 局部降级: {e}")
        from app.models.schemas import DiffCompareSchema

        return {"diff_result": DiffCompareSchema(), "current_agent": 3, "degradation_notes": notes}


def _node4(state: GraphState) -> GraphState:
    diff = state.get("diff_result")
    if not diff:
        from app.models.schemas import RiskReviewSchema

        return {"review_result": RiskReviewSchema(), "current_agent": 4}
    try:
        review = run_agent4(
            diff,
            focus_atom_ids=state.get("focus_atom_ids"),
            extra_context_paths=state.get("extra_context_paths"),
        )
        notes = list(state.get("degradation_notes", []))
        notes.extend(review.degradation_notes)
        review.degradation_notes = []
        return {"review_result": review, "current_agent": 4, "degradation_notes": notes}
    except Exception as e:
        notes = list(state.get("degradation_notes", []))
        notes.append(f"Agent4 局部降级: {e}")
        from app.models.schemas import RiskReviewSchema

        return {"review_result": RiskReviewSchema(degradation_notes=notes), "current_agent": 4, "degradation_notes": notes}


def _node5(state: GraphState) -> GraphState:
    from app.models.schemas import DiffCompareSchema, ProjectIndexSchema, RiskReviewSchema, TaskResultSchema

    base = state.get("base_index") or ProjectIndexSchema()
    head = state.get("head_index") or ProjectIndexSchema()
    diff = state.get("diff_result") or DiffCompareSchema()
    review = state.get("review_result") or RiskReviewSchema()
    try:
        result = run_agent5(
            base,
            head,
            diff,
            review,
            state["pr_context"],
            state.get("project_type"),
            state.get("framework"),
        )
        notes = list(state.get("degradation_notes", []))
        result.degradation_notes = notes + result.degradation_notes
        return {"final_result": result, "current_agent": 5}
    except Exception as e:
        notes = list(state.get("degradation_notes", []))
        notes.append(f"Agent5 局部降级: {e}")

        return {
            "final_result": TaskResultSchema(summary="分析部分完成", degradation_notes=notes),
            "current_agent": 5,
            "degradation_notes": notes,
        }


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
