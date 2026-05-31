"""认证模块测试。"""
from __future__ import annotations

from app.routes.auth import login_handler, logout_handler, profile_handler
from app.services.token_store import TokenStore


def test_login_success_for_admin():
    result = login_handler("admin", "correct-password")
    assert result["ok"] is True
    assert "token" in result


def test_login_failure_for_unknown_user():
    result = login_handler("nobody", "wrong")
    assert result["ok"] is False
    assert result["reason"] == "invalid_credentials"


def test_logout_revokes_token():
    login = login_handler("admin", "correct-password")
    token = login["token"]
    assert logout_handler(token)["ok"] is True
    profile = profile_handler(token)
    assert profile["ok"] is False


def test_token_store_ttl():
    store = TokenStore(default_ttl=60)
    token = store.issue("demo-user")
    assert store.resolve(token) is not None
