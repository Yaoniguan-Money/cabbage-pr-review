from fastapi.testclient import TestClient

from app.local.client_meta import get_error_messages
from app.main import app

client = TestClient(app)


def test_client_meta_api():
    resp = client.get("/api/client-meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error_messages"]["create_task"]
    assert set(body["error_messages"].keys()) == set(get_error_messages().keys())
    assert "use_mock_llm" in body
    assert body["mock_mode_banner"]
