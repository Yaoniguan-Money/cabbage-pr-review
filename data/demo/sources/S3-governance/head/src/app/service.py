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


    def summarize_open_cases(self, *, tenant_id: str) -> dict[str, Any]:
        open_cases = [r for r in self._records if r.tenant_id == tenant_id]
        return {"tenant_id": tenant_id, "open_count": len(open_cases)}

    def bulk_validate(self, payloads: list[dict[str, Any]], *, required: Iterable[str]) -> list[str]:
        errors: list[str] = []
        for index, payload in enumerate(payloads):
            missing = [key for key in required if not payload.get(key)]
            if missing:
                errors.append(f"row {index}: missing {', '.join(missing)}")
        return errors

    def rotate_write_tokens(self) -> int:
        count = len(self._tokens)
        self._tokens.clear()
        return count

    def attach_decision_metadata(self, record: AuditRecord, decision: PolicyDecision) -> dict[str, Any]:
        return {
            "tenant_id": record.tenant_id,
            "resource": record.resource,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "case_id": record.case_id,
        }

    def compute_audit_hash(self, record: AuditRecord) -> str:
        material = f"{record.tenant_id}:{record.resource}:{record.action}:{record.case_id}"
        return hashlib.sha256(material.encode()).hexdigest()

    def list_actions_for_resource(self, resource: str) -> list[str]:
        return sorted({r.action for r in self._records if r.resource == resource})

    def purge_records_before(self, timestamp: float) -> int:
        kept = [r for r in self._records if r.created_at >= timestamp]
        removed = len(self._records) - len(kept)
        self._records = kept
        return removed

    def merge_policy_decisions(self, decisions: list[PolicyDecision]) -> PolicyDecision:
        if not decisions:
            return PolicyDecision(allowed=False, reason="no decisions supplied")
        if all(item.allowed for item in decisions):
            return PolicyDecision(allowed=True, reason="all checks passed")
        blocked = next(item for item in decisions if not item.allowed)
        return PolicyDecision(allowed=False, reason=blocked.reason)

    def format_audit_csv_row(self, record: AuditRecord) -> str:
        return ",".join([record.tenant_id, record.resource, record.action, record.actor, str(record.case_id)])

    def import_policy_bundle(self, bundle: dict[str, Any]) -> int:
        actions = bundle.get("allowed_actions") or []
        added = 0
        for action in actions:
            if action not in self._allowed_actions:
                self._allowed_actions.add(str(action))
                added += 1
        return added

    def count_records_by_action(self, action: str) -> int:
        return sum(1 for record in self._records if record.action == action)

    def latest_record_for_tenant(self, tenant_id: str) -> AuditRecord | None:
        matches = [record for record in self._records if record.tenant_id == tenant_id]
        return matches[-1] if matches else None

    def describe_token_store(self) -> dict[str, int]:
        return {"active_tokens": len(self._tokens)}

    def reset_audit_trail(self) -> None:
        self._records.clear()
        self._tokens.clear()

    def allowed_action_snapshot(self) -> list[str]:
        return sorted(self._allowed_actions)

    def validate_actor_domain(self, actor: str, *, allowed_suffix: str) -> bool:
        return actor.endswith(allowed_suffix)

    def build_policy_report(self, resource: str) -> dict[str, Any]:
        actions = self.list_actions_for_resource(resource)
        return {"resource": resource, "actions": actions, "count": len(actions)}

    def record_digest_for_export(self, record: AuditRecord) -> str:
        return self.compute_audit_hash(record)[:12]


# svc-anchor-01
# svc-anchor-02
# svc-anchor-03
# svc-anchor-04
# svc-anchor-05
