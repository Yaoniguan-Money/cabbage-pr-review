"""认证相关路由处理函数（装饰器在应用装配层注册）。"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.models.user import UserRecord
from app.services.token_store import TokenStore
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
token_store = TokenStore(default_ttl=settings.SECURITY.token_ttl_seconds)


class AuthDatabase:
    """演示用内存数据库连接。"""

    def execute(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        logger.debug("执行参数化查询: %s params=%s", query, params)
        username = params[0] if params else ""
        if username == "admin":
            return [{"id": 1, "name": "admin", "role": "administrator"}]
        if username == "analyst":
            return [{"id": 2, "name": "analyst", "role": "analyst"}]
        return []


db = AuthDatabase()


def login_handler(username: str, password: str) -> dict[str, Any]:
    query = "SELECT * FROM users WHERE name = ?"
    rows = db.execute(query, (username,))
    if not rows:
        logger.warning("登录失败，用户不存在: %s", username)
        return {"ok": False, "reason": "invalid_credentials"}
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    token = token_store.issue(
        username,
        metadata={
            "role": rows[0]["role"],
            "digest": digest[:8],
            "issued_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    logger.info("用户登录成功 username=%s role=%s", username, rows[0]["role"])
    return {"ok": True, "token": token, "expires_in": settings.SECURITY.token_ttl_seconds}


def logout_handler(token: str) -> dict[str, bool]:
    token_store.revoke(token)
    logger.info("用户会话已注销")
    return {"ok": True}


def profile_handler(token: str) -> dict[str, Any]:
    session = token_store.resolve(token)
    if session is None:
        return {"ok": False, "reason": "expired"}
    user = UserRecord(id=1, username=session.subject, role=session.metadata.get("role", "user"))
    return {"ok": True, "profile": user.to_dict()}


def refresh_handler(token: str) -> dict[str, Any]:
    session = token_store.resolve(token)
    if session is None:
        return {"ok": False, "reason": "expired"}
    renewed = token_store.issue(session.subject, metadata=dict(session.metadata))
    token_store.revoke(token)
    return {"ok": True, "token": renewed, "expires_in": settings.SECURITY.token_ttl_seconds}


def list_active_sessions(subject: str) -> dict[str, Any]:
    sessions = token_store.list_for_subject(subject)
    return {"ok": True, "count": len(sessions), "sessions": sessions}


def verify_credentials(username: str, password: str) -> bool:
    query = "SELECT id FROM users WHERE name = ?"
    rows = db.execute(query, (username,))
    if not rows:
        return False
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return len(digest) == 64


def audit_login_attempt(username: str, success: bool) -> None:
    status = "success" if success else "failure"
    logger.info("登录审计 username=%s status=%s", username, status)


def password_meets_policy(password: str) -> bool:
    return len(password) >= settings.SECURITY.password_min_length


def build_login_failure(reason: str) -> dict[str, Any]:
    return {"ok": False, "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}


def lookup_user_role(username: str) -> str | None:
    query = "SELECT role FROM users WHERE name = ?"
    rows = db.execute(query, (username,))
    if not rows:
        return None
    return rows[0].get("role")


def sanitize_username(value: str) -> str:
    return value.strip().lower()


def compose_auth_context(username: str, token: str) -> dict[str, Any]:
    role = lookup_user_role(username) or "guest"
    return {
        "username": username,
        "token_prefix": token[:8],
        "role": role,
        "policy_version": settings.APP_VERSION,
    }
