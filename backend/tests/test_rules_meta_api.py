from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rules_meta_api():
    resp = client.get("/api/rules-meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["visualization_mode"] == "markdown"
    assert "ui_strings" in body
    assert body["ui_strings"]["nav_report"]
    assert body["ui_strings"]["overview_risks_preview_title"]
    assert body["ui_strings"]["back_link"]
