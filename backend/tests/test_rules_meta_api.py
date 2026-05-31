from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rules_meta_api():
    resp = client.get("/api/rules-meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["visualization_mode"] == "diagrams"
    assert "ui_strings" in body
    assert body["ui_strings"]["nav_report"]
    assert body["ui_strings"]["nav_rule_hits"]
    assert body["ui_strings"]["section_index"]


def test_rules_catalog_api():
    resp = client.get("/api/rules-catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rules_count"] >= 10
    assert body["rules_invalid_count"] == 0
    assert body["rules"][0]["id"]
    assert "pattern" not in body["rules"][0]
