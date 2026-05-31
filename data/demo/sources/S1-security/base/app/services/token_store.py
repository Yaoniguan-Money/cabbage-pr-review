"""内存令牌存储，支持 TTL 与撤销。"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionRecord:
    subject: str
    expires_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


class TokenStore:
    def __init__(self, default_ttl: int = 3600) -> None:
        self.default_ttl = default_ttl
        self._sessions: dict[str, SessionRecord] = {}

    def issue(self, subject: str, metadata: dict[str, Any] | None = None) -> str:
        token = secrets.token_urlsafe(24)
        self._sessions[token] = SessionRecord(
            subject=subject,
            expires_at=time.time() + self.default_ttl,
            metadata=metadata or {},
        )
        return token

    def resolve(self, token: str) -> SessionRecord | None:
        record = self._sessions.get(token)
        if record is None:
            return None
        if record.expires_at < time.time():
            self._sessions.pop(token, None)
            return None
        return record

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)

    def purge_expired(self) -> int:
        now = time.time()
        expired = [token for token, record in self._sessions.items() if record.expires_at < now]
        for token in expired:
            self._sessions.pop(token, None)
        return len(expired)
