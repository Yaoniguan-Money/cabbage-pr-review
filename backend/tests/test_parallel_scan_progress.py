import time
from unittest.mock import patch

import pytest

from app.graph.parallel_scan import run_parallel_scan
from app.graph.state import GraphState
from app.models.schemas import InputType, TaskRecord, TaskStatus
from app.services import task_progress
from app.services.task_store import task_store


def _minimal_state() -> GraphState:
    return {
        "pr_context": {
            "title": "Parallel",
            "file_paths": ["a.py"],
            "patches": [{"filename": "a.py", "status": "modified", "patch": "+x"}],
            "changed_files_count": 1,
            "base_ref": "main",
            "head_ref": "feat",
        },
        "llm_mode": "rules_only",
        "degradation_notes": [],
    }


@pytest.mark.parametrize("delay_sec", [0.15])
def test_parallel_scan_both_agents_running_observable(delay_sec: float):
    record = TaskRecord(
        input_type=InputType.PATCH,
        input_value="x",
        status=TaskStatus.RUNNING,
        llm_mode="rules_only",
    )
    record.init_agent_progress()
    task_store._tasks[record.id] = record

    both_running_seen: list[bool] = []
    original_update = task_store.update

    def tracking_update(rec: TaskRecord) -> None:
        original_update(rec)
        if rec.id != record.id:
            return
        ap0, ap1 = rec.agent_progress[0], rec.agent_progress[1]
        if ap0.status == "running" and ap1.status == "running":
            both_running_seen.append(True)

    task_store.update = tracking_update  # type: ignore[method-assign]

    def slow_rules_node1(state: GraphState) -> GraphState:
        time.sleep(delay_sec)
        from app.rules.workflow_nodes import rules_node1

        return rules_node1(state)

    def slow_rules_node2(state: GraphState) -> GraphState:
        time.sleep(delay_sec)
        from app.rules.workflow_nodes import rules_node2

        return rules_node2(state)

    task_progress.bind_task_progress(record.id)
    try:
        with (
            patch("app.graph.parallel_scan.rules_node1", slow_rules_node1),
            patch("app.graph.parallel_scan.rules_node2", slow_rules_node2),
        ):
            run_parallel_scan(_minimal_state())
    finally:
        task_store.update = original_update  # type: ignore[method-assign]
        task_progress.clear_task_progress()

    assert both_running_seen, "应观测到 agent1 与 agent2 同时为 running"
    updated = task_store.get(record.id)
    assert updated is not None
    assert updated.agent_progress[0].status == "completed"
    assert updated.agent_progress[1].status == "completed"
