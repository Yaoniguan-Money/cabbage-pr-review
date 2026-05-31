from app.agents.agent1_base_scan import run_agent1
from app.agents.agent2_head_scan import run_agent2
from app.agents.agent3_diff import run_agent3
from app.agents.agent4_review import run_agent4
from app.agents.agent5_visualize import run_agent5
from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES
from app.models.schemas import ProjectIndexSchema


SAMPLE_CONTEXT = {
    "title": "Add FastAPI route",
    "file_paths": ["app/main.py", "app/routes/api.py"],
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
    "readme": "# Demo API",
    "tree": ["app/", "app/main.py"],
    "entry_files": ["app/main.py"],
    "base_file_contents": {"app/main.py": "from fastapi import FastAPI"},
    "head_file_contents": {"app/routes/api.py": "@app.get('/health')"},
}


def test_agent_pipeline_schema():
    base, _ = run_agent1(SAMPLE_CONTEXT)
    head, _ = run_agent2(SAMPLE_CONTEXT)
    assert isinstance(base, ProjectIndexSchema)
    assert base.version == "base"
    assert head.version == "head"
    assert base.architecture_diagram and base.architecture_diagram.nodes
    diff, _ = run_agent3(base, head, SAMPLE_CONTEXT)
    assert diff.all_atoms
    review, _, stats = run_agent4(diff, base, head, SAMPLE_CONTEXT)
    assert review.risks
    assert review.risks[0].evidence
    assert stats.reviewed_atoms >= 1
    result, _ = run_agent5(base, head, diff, review, SAMPLE_CONTEXT, None, None, review_stats=stats)
    assert result.summary
    assert len(result.diagrams) == len(SCHEMA_DIAGRAM_TYPES)
    diagram_types = {d.diagram_type for d in result.diagrams}
    assert diagram_types == set(SCHEMA_DIAGRAM_TYPES)
    for diagram in result.diagrams:
        assert diagram.mermaid.strip()
    assert result.detected_framework
