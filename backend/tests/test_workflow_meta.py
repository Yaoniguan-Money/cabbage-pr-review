from app.local.workflow_meta import (
    AGENT_NODE_ORDER,
    PARALLEL_GROUP_SCAN,
    WORKFLOW_NODE_AGENT_MAP,
    get_agent_step_definitions,
)
from app.models.schemas import TaskRecord, TaskStatus, InputType


def test_agent_step_definitions_include_parallel_group_for_scan():
    steps = get_agent_step_definitions()
    assert len(steps) == 5
    scan_steps = [s for s in steps if s.get("parallel_group") == PARALLEL_GROUP_SCAN]
    assert len(scan_steps) == 2
    assert scan_steps[0]["agent_id"] == 1
    assert scan_steps[1]["agent_id"] == 2
    assert scan_steps[0]["name"]
    assert scan_steps[1]["name"]


def test_workflow_node_order_and_map():
    assert AGENT_NODE_ORDER[0] == "scan_parallel"
    assert WORKFLOW_NODE_AGENT_MAP["scan_parallel"] == [1, 2]
    assert WORKFLOW_NODE_AGENT_MAP["agent3"] == [3]


def test_init_agent_progress_uses_workflow_meta():
    record = TaskRecord(
        input_type=InputType.PATCH,
        input_value="",
        status=TaskStatus.PENDING,
    )
    record.init_agent_progress()
    assert record.agent_progress[0].parallel_group == PARALLEL_GROUP_SCAN
    assert record.agent_progress[1].parallel_group == PARALLEL_GROUP_SCAN
    assert record.agent_progress[2].parallel_group is None
    assert record.agent_progress[0].name == get_agent_step_definitions()[0]["name"]
