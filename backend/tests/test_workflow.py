import pytest

from app.agents.llm_helpers import LLMRequiredError
from app.graph import workflow as workflow_module
from app.graph.workflow import workflow_app


@pytest.mark.asyncio
async def test_workflow_invoke_patch_context():
    state = {
        "pr_context": {
            "title": "Test",
            "file_paths": ["src/main.py"],
            "patches": [{"filename": "src/main.py", "status": "modified", "patch": "+print('hi')"}],
            "changed_files_count": 1,
            "base_ref": "main",
            "head_ref": "feat",
        },
        "project_type": None,
        "framework": None,
        "focus_atom_ids": [],
        "extra_context_paths": [],
        "degradation_notes": [],
    }
    final = await workflow_app.ainvoke(state)
    assert final.get("final_result") is not None
    assert final["final_result"].summary
    assert final["agent_outcomes"][5] == "ok"


@pytest.mark.asyncio
async def test_workflow_marks_auth_failure_as_failed(monkeypatch: pytest.MonkeyPatch):
    def _boom(*_args, **_kwargs):
        raise LLMRequiredError("invalid api key")

    monkeypatch.setattr(workflow_module, "run_agent4", _boom)
    state = {
        "pr_context": {
            "title": "Test",
            "file_paths": ["src/main.py"],
            "patches": [{"filename": "src/main.py", "status": "modified", "patch": "+print('hi')"}],
            "changed_files_count": 1,
            "base_ref": "main",
            "head_ref": "feat",
        },
        "project_type": None,
        "framework": None,
        "focus_atom_ids": [],
        "extra_context_paths": [],
        "degradation_notes": [],
        "agent_outcomes": {},
        "agent_errors": {},
    }
    final = await workflow_app.ainvoke(state)
    assert final["agent_outcomes"][4] == "failed"
    assert any(note.startswith("FAILED/Agent4:") for note in final["degradation_notes"])
