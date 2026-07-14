import pytest

from app.graph.workflow import workflow_app


@pytest.mark.asyncio
async def test_workflow_rules_only_produces_markdown_report():
    state = {
        "pr_context": {
            "title": "Rules Test",
            "file_paths": ["src/auth.py"],
            "patches": [
                {
                    "filename": "src/auth.py",
                    "status": "modified",
                    "patch": '+password = "test-only-placeholder"\n',
                }
            ],
            "changed_files_count": 1,
            "base_ref": "main",
            "head_ref": "feat",
        },
        "project_type": "python-api",
        "framework": "FastAPI",
        "focus_atom_ids": [],
        "extra_context_paths": [],
        "review_depth_mode": "balanced",
        "llm_mode": "rules_only",
        "degradation_notes": [],
        "rule_hits": [],
    }
    final = await workflow_app.ainvoke(state)
    result = final.get("final_result")
    assert result is not None
    assert result.markdown_report.strip()
    assert result.summary.strip()
