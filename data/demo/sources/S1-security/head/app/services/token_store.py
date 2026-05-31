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

    def list_for_subject(self, subject: str) -> list[dict[str, Any]]:
        now = time.time()
        results: list[dict[str, Any]] = []
        for token, record in self._sessions.items():
            if record.subject != subject or record.expires_at < now:
                continue
            results.append(
                {
                    "token_prefix": token[:8],
                    "expires_at": record.expires_at,
                    "metadata": dict(record.metadata),
                }
            )
        return results

    def active_count(self) -> int:
        now = time.time()
        return sum(1 for record in self._sessions.values() if record.expires_at >= now)

    def extend(self, token: str, extra_seconds: int) -> bool:
        record = self.resolve(token)
        if record is None:
            return False
        record.expires_at += extra_seconds
        self._sessions[token] = record
        return True

    def rotate(self, token: str) -> str | None:
        record = self.resolve(token)
        if record is None:
            return None
        self.revoke(token)
        return self.issue(record.subject, metadata=dict(record.metadata))

    def snapshot(self) -> dict[str, int]:
        return {
            "active": self.active_count(),
            "total": len(self._sessions),
        }

    def describe_record(self, token: str) -> dict[str, Any] | None:
        record = self.resolve(token)
        if record is None:
            return None
        return {
            "subject": record.subject,
            "expires_in": max(0, int(record.expires_at - time.time())),
            "metadata_keys": sorted(record.metadata.keys()),
        }
