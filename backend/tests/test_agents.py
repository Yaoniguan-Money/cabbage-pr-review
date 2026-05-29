from app.agents.agent1_base_scan import run_agent1
from app.agents.agent2_head_scan import run_agent2
from app.agents.agent3_diff import run_agent3
from app.agents.agent4_review import run_agent4
from app.agents.agent5_visualize import run_agent5
from app.models.schemas import ProjectIndexSchema


SAMPLE_CONTEXT = {
    "title": "Add FastAPI route",
    "file_paths": ["app/main.py", "app/routes/api.py", "tests/test_api.py"],
    "patches": [
        {
            "filename": "app/routes/api.py",
            "status": "modified",
            "patch": "+@app.get('/health')\n+def health():\n+    return {'ok': True}",
        }
    ],
    "changed_files_count": 2,
    "base_ref": "main",
    "head_ref": "feature",
}


def test_agent_pipeline_schema():
    base = run_agent1(SAMPLE_CONTEXT)
    head = run_agent2(SAMPLE_CONTEXT)
    assert isinstance(base, ProjectIndexSchema)
    diff = run_agent3(base, head, SAMPLE_CONTEXT)
    assert diff.all_atoms
    review = run_agent4(diff)
    assert review.risks
    result = run_agent5(base, head, diff, review, SAMPLE_CONTEXT, None, None)
    assert result.summary
    assert len(result.diagrams) >= 1
    assert result.detected_framework
