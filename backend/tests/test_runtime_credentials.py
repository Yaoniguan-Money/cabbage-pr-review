"""运行时凭据与 public 部署模式。"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.llm.credentials_resolve import (
    cloud_available_for_request,
    resolve_cloud_config,
    resolve_github_token,
    server_cloud_configured,
    server_github_configured,
)
from app.local.runtime_config_meta import RUNTIME_CREDENTIALS_ONBOARDING
from app.main import app
from app.models.schemas import RuntimeCredentials

client = TestClient(app)


def test_public_deploy_ignores_server_key(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-server-should-ignore")
    monkeypatch.setattr(settings, "cloud_api_key", "")
    assert server_cloud_configured() is False
    assert cloud_available_for_request(None) is False
    assert (
        cloud_available_for_request(RuntimeCredentials(cloud_api_key="sk-user")) is True
    )


def test_local_deploy_uses_server_key(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "local")
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-local")
    monkeypatch.setattr(settings, "cloud_api_key", "")
    assert server_cloud_configured() is True
    resolved = resolve_cloud_config(None)
    assert resolved is not None
    assert resolved.api_key == "sk-local"


def test_runtime_config_meta_onboarding_text(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "use_mock_llm", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    resp = client.get("/api/runtime-config-meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ui_strings"]["onboarding_banner"] == RUNTIME_CREDENTIALS_ONBOARDING
    assert body["is_public_deploy"] is True


def test_create_task_cloud_only_requires_runtime_key_on_public(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "use_mock_llm", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "cloud_api_key", "")
    resp = client.post(
        "/api/tasks",
        json={
            "input_type": "patch",
            "value": "diff --git a/foo b/foo\n+line\n",
            "llm_mode": "cloud_only",
        },
    )
    assert resp.status_code == 503


def test_public_deploy_ignores_server_github_token(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "github_token", "ghp-server-should-ignore")
    assert server_github_configured() is False
    assert resolve_github_token(None) == ""


def test_local_deploy_can_disable_server_github_token(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "local")
    monkeypatch.setattr(settings, "github_token", "ghp-local")
    monkeypatch.setattr(settings, "use_server_github_token", False)
    assert server_github_configured() is False
    assert resolve_github_token(None) == ""


def test_public_pr_url_requires_runtime_github_token(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "use_mock_llm", True)
    resp = client.post(
        "/api/tasks",
        json={
            "input_type": "pr_url",
            "value": "https://github.com/octocat/Hello-World/pull/1",
            "llm_mode": "rules_only",
        },
    )
    assert resp.status_code == 400


def test_llm_mode_options_with_runtime_key_query(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "use_mock_llm", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    r0 = client.get("/api/llm-mode-options")
    assert r0.json()["cloud_available"] is False
    r1 = client.get("/api/llm-mode-options?has_runtime_cloud_key=true")
    assert r1.json()["cloud_available"] is True
