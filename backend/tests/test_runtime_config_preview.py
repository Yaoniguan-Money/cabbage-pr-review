from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_runtime_config_preview_with_runtime_key():
    resp = client.post(
        "/api/runtime-config/preview",
        json={
            "runtime_credentials": {
                "cloud_api_key": "sk-test",
                "cloud_api_base": "https://api.deepseek.com",
            }
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "cloud_available" in body
    assert "github_token_configured" in body
    assert "local_available" in body


def test_input_page_meta_has_warm_tips_and_usage_guide():
    resp = client.get("/api/input-page-meta")
    assert resp.status_code == 200
    body = resp.json()
    ui = body["ui_strings"]
    assert ui["credentials_warm_tips_title"] == "温馨提示"
    guide = body["usage_guide"]
    assert guide["title"] == "使用说明"
    assert len(guide["sections"]) >= 2
    assert "不会在服务器上保存" in guide["sections"][0]["paragraphs"][0]
