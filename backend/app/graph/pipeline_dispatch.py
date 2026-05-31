"""规则 / LLM 双 pipeline 分发。"""

from __future__ import annotations

from collections.abc import Callable

from app.graph.state import GraphState
from app.local.llm_mode import is_rules_only_mode

NodeRunner = Callable[[GraphState], GraphState]


def dispatch_node(state: GraphState, rules_runner: NodeRunner, llm_runner: NodeRunner) -> GraphState:
    if is_rules_only_mode(state.get("llm_mode")):
        return rules_runner(state)
    return llm_runner(state)
