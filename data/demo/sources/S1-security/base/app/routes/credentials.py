"""认证相关路由处理函数（装饰器在应用装配层注册）。"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

from fastapi import APIRouter

from app.models.user import UserRecord
from app.services.token_store import TokenStore

logger = logging.getLogger(__name__)
router = APIRouter()
token_store = TokenStore(default_ttl=3600)


class AuthDatabase:
    """演示用内存数据库连接。"""

    def execute(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        logger.debug("执行参数化查询: %s params=%s", query, params)
        username = params[0] if params else ""
        if username == "admin":
            return [{"id": 1, "name": "admin", "role": "administrator"}]
        return []


db = AuthDatabase()


def login_handler(username: str, password: str) -> dict[str, Any]:
    query = "SELECT * FROM users WHERE name = ?"
    rows = db.execute(query, (username,))
    if not rows:
        logger.warning("登录失败，用户不存在: %s", username)
        return {"ok": False, "reason": "invalid_credentials"}
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    token = token_store.issue(username, metadata={"role": rows[0]["role"], "digest": digest[:8]})
    return {"ok": True, "token": token}


def logout_handler(token: str) -> dict[str, bool]:
    token_store.revoke(token)
    return {"ok": True}


def profile_handler(token: str) -> dict[str, Any]:
    session = token_store.resolve(token)
    if session is None:
        return {"ok": False, "reason": "expired"}
    user = UserRecord(id=1, username=session.subject, role=session.metadata.get("role", "user"))
    return {"ok": True, "profile": user.to_dict()}
