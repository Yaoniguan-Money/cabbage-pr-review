"""工作流 Agent 步骤与节点映射单源（禁止在 schemas / 前端硬编码步骤名）。"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentStepDefinition(TypedDict):
    agent_id: int
    name: str
    parallel_group: str | None


PARALLEL_GROUP_SCAN = "scan"

AGENT_STEP_DEFINITIONS: list[AgentStepDefinition] = [
    {"agent_id": 1, "name": "原版本扫描", "parallel_group": PARALLEL_GROUP_SCAN},
    {"agent_id": 2, "name": "PR 版本扫描", "parallel_group": PARALLEL_GROUP_SCAN},
    {"agent_id": 3, "name": "差异对比", "parallel_group": None},
    {"agent_id": 4, "name": "递进式审阅", "parallel_group": None},
    {"agent_id": 5, "name": "可视化组织", "parallel_group": None},
]

AGENT_NODE_ORDER: list[str] = ["scan_parallel", "agent3", "agent4", "agent5"]

WORKFLOW_NODE_AGENT_MAP: dict[str, list[int]] = {
    "scan_parallel": [1, 2],
    "agent3": [3],
    "agent4": [4],
    "agent5": [5],
}


def get_agent_step_definitions() -> list[AgentStepDefinition]:
    return list(AGENT_STEP_DEFINITIONS)


def get_workflow_node_agent_map() -> dict[str, list[int]]:
    return dict(WORKFLOW_NODE_AGENT_MAP)


def list_workflow_meta() -> dict[str, Any]:
    return {
        "agent_steps": get_agent_step_definitions(),
        "node_agent_map": get_workflow_node_agent_map(),
        "node_order": list(AGENT_NODE_ORDER),
    }
