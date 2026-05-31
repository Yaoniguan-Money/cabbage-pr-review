"""治理服务核心逻辑（无 Web 框架装饰器）。"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.models import AuditRecord, PolicyDecision


class ValidationError(ValueError):
    """提交体校验失败。"""


@dataclass
class GovernanceService:
    """内存实现的治理编排服务。"""

    _records: list[AuditRecord] = field(default_factory=list)
    _tokens: dict[str, int] = field(default_factory=dict)
    _allowed_actions: set[str] = field(default_factory=lambda: {"approve", "escalate"})

    def validate_submission(self, payload: dict[str, Any], *, required: Iterable[str]) -> None:
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ValidationError(f"missing fields: {', '.join(missing)}")

    def create_audit_record(
        self,
        *,
        tenant_id: str,
        resource: str,
        action: str,
        actor: str,
        case_id: int,
    ) -> AuditRecord:
        self.validate_submission(
            {"tenant_id": tenant_id, "resource": resource, "action": action, "actor": actor},
            required=("tenant_id", "resource", "action", "actor"),
        )
        record = AuditRecord(
            tenant_id=tenant_id,
            resource=resource,
            action=action,
            actor=actor,
            case_id=case_id,
            created_at=time.time(),
        )
        self._records.append(record)
        return record

    def is_action_allowed(self, action: str) -> bool:
        return action in self._allowed_actions

    def evaluate_policy(self, action: str, *, severity: str = "medium") -> PolicyDecision:
        if action in self._allowed_actions:
            return PolicyDecision(allowed=True, reason=f"{action} permitted at {severity}")
        return PolicyDecision(allowed=False, reason=f"{action} blocked by policy")

    def issue_write_token(self, *, version: int) -> str:
        digest = hashlib.sha256(f"write:{version}:{time.time()}".encode()).hexdigest()
        self._tokens[digest] = version
        return digest

    def check_write_token(self, token: str, *, expected_version: int) -> bool:
        return self._tokens.get(token) == expected_version

    def export_snapshot(self) -> dict[str, int]:
        return {"records": len(self._records), "tokens": len(self._tokens)}


# svc-anchor-01
# svc-anchor-02
# svc-anchor-03
# svc-anchor-04
# svc-anchor-05
