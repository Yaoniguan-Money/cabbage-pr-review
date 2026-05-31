from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_detail_page_meta_api():
    resp = client.get("/api/detail-page-meta")
    assert resp.status_code == 200
    body = resp.json()
    ui = body["ui_strings"]
    assert ui["nav_files"]
    assert ui["diff_empty"]
    assert ui["status_running"]
    assert ui["task_id_toggle_show"]
    assert ui["agent_stepper_label"]
    assert "{ref}" in ui["branch_into"]
