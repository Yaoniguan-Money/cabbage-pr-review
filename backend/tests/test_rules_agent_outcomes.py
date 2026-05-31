"""规则 workflow 节点须写入 agent_outcomes，与 LLM 路径一致。"""

from unittest.mock import patch

import pytest

from app.graph.state import GraphState
from app.models.schemas import DiffCompareSchema
from app.rules.workflow_nodes import rules_node1, rules_node3


def _minimal_state(**extra) -> GraphState:
    base: GraphState = {
        "pr_context": {"patches": [], "file_paths": []},
        "degradation_notes": [],
        "agent_outcomes": {},
        "agent_errors": {},
    }
    base.update(extra)
    return base


def test_rules_node1_exception_sets_degraded_outcome():
    with patch("app.rules.workflow_nodes.run_rules_index", side_effect=RuntimeError("index boom")):
        out = rules_node1(_minimal_state())
    assert out["agent_outcomes"].get(1) == "degraded"
    assert 1 in out.get("agent_errors", {})


def test_rules_node3_empty_diff_sets_failed_outcome():
    empty_diff = DiffCompareSchema(all_atoms=[])
    with patch("app.rules.workflow_nodes.load_rule_pack") as load_pack, patch(
        "app.rules.workflow_nodes.run_rules_diff",
        return_value=(empty_diff, []),
    ):
        load_pack.return_value = (None, type("Cfg", (), {"scope": type("S", (), {
            "ignore_path_patterns": [],
            "max_atoms_per_run": 100,
            "split_patch_hunks": True,
        })()})())
        out = rules_node3(_minimal_state())
    assert out["agent_outcomes"].get(3) == "failed"


def test_rules_node3_success_sets_ok_outcome():
    from app.models.schemas import DiffAtom

    diff = DiffCompareSchema(
        all_atoms=[
            DiffAtom(
                id="a1",
                file_path="x.py",
                change_type="modified",
                symbol="",
                summary="s",
            )
        ]
    )
    with patch("app.rules.workflow_nodes.load_rule_pack") as load_pack, patch(
        "app.rules.workflow_nodes.run_rules_diff",
        return_value=(diff, []),
    ):
        load_pack.return_value = (None, type("Cfg", (), {"scope": type("S", (), {
            "ignore_path_patterns": [],
            "max_atoms_per_run": 100,
            "split_patch_hunks": True,
        })()})())
        out = rules_node3(_minimal_state())
    assert out["agent_outcomes"].get(3) == "ok"
