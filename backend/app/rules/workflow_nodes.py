"""规则模式 workflow 节点（与 agents/ 隔离）。"""

from __future__ import annotations

from app.graph.state import GraphState
from app.graph.workflow_helpers import (
    EmptyAgentResultError,
    empty_base,
    empty_head,
    run_rules_node_safe,
)
from app.local.review_depth import get_review_depth_option
from app.models.schemas import DiffCompareSchema, RiskReviewSchema, TaskResultSchema
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_index import run_rules_index
from app.rules.pipeline.rules_markdown import run_rules_finalize
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_loader import load_rule_pack


def rules_node1(state: GraphState) -> GraphState:
    def _run() -> dict:
        base, notes = run_rules_index(state["pr_context"], version="base")
        return {"base_index": base, "degradation_notes": notes}

    return run_rules_node_safe(
        state,
        1,
        _run,
        fallback={"base_index": empty_base()},
    )


def rules_node2(state: GraphState) -> GraphState:
    def _run() -> dict:
        head, notes = run_rules_index(state["pr_context"], version="head")
        return {"head_index": head, "degradation_notes": notes}

    return run_rules_node_safe(
        state,
        2,
        _run,
        fallback={"head_index": empty_head()},
    )


def rules_node3(state: GraphState) -> GraphState:
    def _run() -> dict:
        _, pack_config = load_rule_pack()
        diff, notes = run_rules_diff(
            state["pr_context"],
            ignore_patterns=pack_config.scope.ignore_path_patterns,
            max_atoms=pack_config.scope.max_atoms_per_run,
            split_patch_hunks=pack_config.scope.split_patch_hunks,
        )
        return {"diff_result": diff, "degradation_notes": notes}

    def _validate(payload: dict) -> None:
        diff = payload.get("diff_result")
        if not diff or not diff.all_atoms:
            raise EmptyAgentResultError("diff_result has no atoms")

    return run_rules_node_safe(
        state,
        3,
        _run,
        fallback={"diff_result": DiffCompareSchema()},
        validator=_validate,
        empty_is_fatal=True,
    )


def rules_node4(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    depth_mode = state.get("review_depth_mode") or "balanced"
    depth_opt = get_review_depth_option(depth_mode)

    def _run() -> dict:
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
            "degradation_notes": notes,
        }

    return run_rules_node_safe(
        state,
        4,
        _run,
        fallback={"review_result": RiskReviewSchema()},
    )


def rules_node5(state: GraphState) -> GraphState:
    diff = state.get("diff_result") or DiffCompareSchema()
    review = state.get("review_result") or RiskReviewSchema()
    hits = list(state.get("rule_hits") or [])

    def _run() -> dict:
        result = run_rules_finalize(
            diff=diff,
            review=review,
            hits=hits,
            review_stats=state.get("review_stats"),
            project_type=state.get("project_type"),
            framework=state.get("framework"),
            extra_notes=state.get("degradation_notes"),
            base_index=state.get("base_index"),
            head_index=state.get("head_index"),
            pr_context=state.get("pr_context") or {},
        )
        return {"final_result": result, "degradation_notes": []}

    return run_rules_node_safe(
        state,
        5,
        _run,
        fallback={"final_result": TaskResultSchema(summary="", degradation_notes=[])},
    )
