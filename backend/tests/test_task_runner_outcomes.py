import pytest

from app.agents.llm_helpers import LLMRequiredError
from app.graph import workflow as workflow_module
from app.models.schemas import InputType, MissingInfoItem, RiskReviewSchema, TaskOutcome, TaskRecord, TaskStatus
from app.services.task_runner import execute_task


def _make_patch_record() -> TaskRecord:
    record = TaskRecord(
        input_type=InputType.PATCH,
        input_value="diff --git a/src/main.py b/src/main.py\n+print('hi')\n",
    )
    record.init_agent_progress()
    return record


@pytest.mark.asyncio
async def test_execute_task_fails_on_agent4_auth_error(monkeypatch: pytest.MonkeyPatch):
    def _boom(*_args, **_kwargs):
        raise LLMRequiredError("invalid api key")

    monkeypatch.setattr(workflow_module, "run_agent4", _boom)
    record = _make_patch_record()

    await execute_task(record)

    assert record.status == TaskStatus.FAILED
    assert record.outcome == TaskOutcome.FAILED
    assert record.result is None
    assert record.error_message
    assert "Agent4" in record.error_message
    assert any(note.startswith("FAILED/Agent4:") for note in record.degradation_notes)


@pytest.mark.asyncio
async def test_execute_task_completes_with_degraded_outcome(monkeypatch: pytest.MonkeyPatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("base scan timeout")

    monkeypatch.setattr(workflow_module, "run_agent1", _boom)
    record = _make_patch_record()

    await execute_task(record)

    assert record.status == TaskStatus.COMPLETED
    assert record.outcome == TaskOutcome.DEGRADED
    assert record.result is not None
    assert any(note.startswith("DEGRADED/Agent1:") for note in record.degradation_notes)
    assert any(ap.agent_id == 1 and ap.status == "degraded" for ap in record.agent_progress)


@pytest.mark.asyncio
async def test_execute_task_keeps_rules_only_patch_completed(monkeypatch: pytest.MonkeyPatch):
    def _rules_only(*_args, **_kwargs):
        return (
            RiskReviewSchema(
                risks=[],
                missing_info=[MissingInfoItem(module="rules", reason="rules-only patch")],
                degradation_notes=[],
            ),
            [],
            None,
        )

    monkeypatch.setattr(workflow_module, "run_agent4", _rules_only)
    record = _make_patch_record()

    await execute_task(record)

    assert record.status == TaskStatus.COMPLETED
    assert record.outcome == TaskOutcome.OK
    assert record.result is not None
    assert record.result.risks == []
