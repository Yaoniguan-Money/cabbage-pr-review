"""client_meta 云端不可用横幅单源。"""

from app.config import settings
from app.local.client_meta import CLOUD_UNAVAILABLE_BANNER, cloud_unavailable_banner


def test_cloud_unavailable_banner_empty_when_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "use_mock_llm", True)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    assert cloud_unavailable_banner() == ""


def test_cloud_unavailable_banner_when_no_cloud_key(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "local")
    monkeypatch.setattr(settings, "use_mock_llm", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "cloud_api_key", "")
    monkeypatch.setattr("app.llm.router.cloud_available", lambda: False)
    assert cloud_unavailable_banner() == CLOUD_UNAVAILABLE_BANNER


def test_public_deploy_onboarding_banner(monkeypatch):
    monkeypatch.setattr(settings, "deploy_mode", "public")
    monkeypatch.setattr(settings, "use_mock_llm", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    from app.local.runtime_config_meta import RUNTIME_CREDENTIALS_ONBOARDING

    assert cloud_unavailable_banner() == RUNTIME_CREDENTIALS_ONBOARDING
