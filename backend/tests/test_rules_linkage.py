from fastapi.testclient import TestClient

from app.main import app
from app.rules.rule_loader import resolve_rules_pack_dir

client = TestClient(app)


def test_health_includes_rules_diagnostics():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_mode_count"] == 4
    assert body["rules_pack_loaded"] is True
    assert body["rules_count"] >= 10


def test_create_task_includes_visualization_mode():
    resp = client.post(
        "/api/tasks",
        json={
            "input_type": "patch",
            "value": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -0,0 +1 @@\n+x=1",
            "llm_mode": "rules_only",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_mode"] == "rules_only"
    assert body["visualization_mode"] == "markdown"
    assert body["rerun_supported"] is False
    assert resolve_rules_pack_dir().is_dir()
