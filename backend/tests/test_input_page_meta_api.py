from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_input_page_meta_api():
    resp = client.get("/api/input-page-meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_types"]
    assert body["frameworks"]
    assert body["input_tabs"]
    assert body["ui_strings"]["submit_idle"]
    assert body["default_project_type"] == "unknown"
