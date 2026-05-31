"""认证模块测试。"""
from __future__ import annotations

from app.models.user import UserRecord
from app.routes.auth import (
    audit_login_attempt,
    compose_auth_context,
    login_handler,
    logout_handler,
    password_meets_policy,
    profile_handler,
    refresh_handler,
    sanitize_username,
    verify_credentials,
)
from app.services.token_store import TokenStore


def test_login_success_for_admin():
    result = login_handler("admin", "correct-password")
    assert result["ok"] is True
    assert "token" in result
    assert result["expires_in"] > 0


def test_login_success_for_analyst():
    result = login_handler("analyst", "correct-password")
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


def test_refresh_rotates_token():
    login = login_handler("admin", "correct-password")
    old_token = login["token"]
    refreshed = refresh_handler(old_token)
    assert refreshed["ok"] is True
    assert refreshed["token"] != old_token
    assert profile_handler(old_token)["ok"] is False


def test_token_store_ttl():
    store = TokenStore(default_ttl=60)
    token = store.issue("demo-user")
    assert store.resolve(token) is not None


def test_token_store_list_for_subject():
    store = TokenStore(default_ttl=60)
    store.issue("alice")
    store.issue("alice")
    store.issue("bob")
    sessions = store.list_for_subject("alice")
    assert len(sessions) == 2


def test_password_policy():
    assert password_meets_policy("short") is False
    assert password_meets_policy("long-enough") is True


def test_verify_credentials():
    assert verify_credentials("admin", "correct-password") is True
    assert verify_credentials("ghost", "nope") is False


def test_user_permissions():
    admin = UserRecord(id=1, username="admin", role="administrator")
    analyst = UserRecord(id=2, username="analyst", role="analyst")
    assert admin.can_access("admin_panel") is True
    assert analyst.can_access("admin_panel") is False
    assert analyst.can_access("audit_log") is True


def test_sanitize_username():
    assert sanitize_username(" Admin ") == "admin"


def test_compose_auth_context():
    login = login_handler("admin", "correct-password")
    context = compose_auth_context("admin", login["token"])
    assert context["role"] == "administrator"
    assert context["token_prefix"]


def test_audit_login_attempt_does_not_raise():
    audit_login_attempt("admin", True)
    audit_login_attempt("admin", False)
