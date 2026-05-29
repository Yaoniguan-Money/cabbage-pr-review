import pytest

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
