from fastapi.testclient import TestClient

from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES
from app.main import app

client = TestClient(app)


def test_diagram_meta_api_contract():
    resp = client.get("/api/diagram-meta")
    assert resp.status_code == 200
    data = resp.json()
    assert "section_label" in data
    assert "ui_strings" in data
    assert "render_error_title" in data["ui_strings"]
    assert "default_legend" in data
    assert len(data["diagram_types"]) == len(SCHEMA_DIAGRAM_TYPES)
    ids = [t["id"] for t in data["diagram_types"]]
    assert ids == list(SCHEMA_DIAGRAM_TYPES)
    for item in data["diagram_types"]:
        assert item["default_title"]
        assert item["description"]
        assert item["layout"]
