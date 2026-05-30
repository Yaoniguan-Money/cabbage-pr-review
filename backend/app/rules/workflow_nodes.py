"""规则模式 workflow 节点（与 agents/ 隔离）。"""

from __future__ import annotations

from app.graph.state import GraphState
from app.graph.workflow_helpers import empty_base, empty_head, merge_notes
from app.local.review_depth import get_review_depth_option
from app.models.schemas import DiffCompareSchema, RiskReviewSchema, TaskResultSchema
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_index import run_rules_index
from app.rules.pipeline.rules_markdown import run_rules_finalize
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_loader import load_rule_pack


def rules_node1(state: GraphState) -> GraphState:
    try:
        base, notes = run_rules_index(state["pr_context"], version="base")
        return {"base_index": base, "current_agent": 1, "degradation_notes": merge_notes(state, notes)}
    except Exception as exc:
        return {
            "base_index": empty_base(),
            "current_agent": 1,
            "degradation_notes": merge_notes(state, [f"规则索引(base) 局部降级: {exc}"]),
        }


def rules_node2(state: GraphState) -> GraphState:
    try:
        head, notes = run_rules_index(state["pr_context"], version="head")
        return {"head_index": head, "current_agent": 2, "degradation_notes": merge_notes(state, notes)}
    except Exception as exc:
        return {
            "head_index": empty_head(),
            "current_agent": 2,
            "degradation_notes": merge_notes(state, [f"规则索引(head) 局部降级: {exc}"]),
        }


def rules_node3(state: GraphState) -> GraphState:
    try:
        _, pack_config = load_rule_pack()
        diff, notes = run_rules_diff(
            state["pr_context"],
            ignore_patterns=pack_config.scope.ignore_path_patterns,
            max_atoms=pack_config.scope.max_atoms_per_run,
        )
        return {"diff_result": diff, "current_agent": 3, "degradation_notes": merge_notes(state, notes)}
    except Exception as exc:
        return {
            "diff_result": DiffCompareSchema(),
            "current_agent": 3,
            "degradation_notes": merge_notes(state, [f"规则 diff 局部降级: {exc}"]),
        }


def rules_node4(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    depth_mode = state.get("review_depth_mode") or "balanced"
    depth_opt = get_review_depth_option(depth_mode)
    try:
        review, hits, stats, notes = run_rules_review(
            diff,
            state["pr_context"],
            review_depth_mode=depth_mode,
        )
        stats.review_depth_label = depth_opt.label
        state_hits = list(state.get("rule_hits") or [])
        state_hits.extend(hits)
        return {
            "review_result": review,
            "review_stats": stats,
            "rule_hits": state_hits,
            "current_agent": 4,
            "degradation_notes": merge_notes(state, notes),
        }
    except Exception as exc:
        return {
            "review_result": RiskReviewSchema(degradation_notes=[str(exc)]),
            "current_agent": 4,
            "degradation_notes": merge_notes(state, [f"规则审阅局部降级: {exc}"]),
        }


def rules_node5(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    review = state.get("review_result") or RiskReviewSchema()
    hits = list(state.get("rule_hits") or [])
    try:
        result = run_rules_finalize(
            diff=diff,
            review=review,
            hits=hits,
            review_stats=state.get("review_stats"),
            project_type=state.get("project_type"),
            framework=state.get("framework"),
            extra_notes=state.get("degradation_notes"),
        )
        return {"final_result": result, "current_agent": 5, "degradation_notes": merge_notes(state, [])}
    except Exception as exc:
        return {
            "final_result": TaskResultSchema(summary="", degradation_notes=[str(exc)]),
            "current_agent": 5,
            "degradation_notes": merge_notes(state, [f"规则报告局部降级: {exc}"]),
        }
