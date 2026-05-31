"""治理域数据模型。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AuditRecord:
    tenant_id: str
    resource: str
    action: str
    actor: str
    case_id: int
    created_at: float


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(slots=True)
class TenantProfile:
    tenant_id: str
    display_name: str
    contact_email: str
    retention_days: int = 90


@dataclass
class ComplianceBundle:
    bundle_id: str
    version: str
    controls: list[str] = field(default_factory=list)

    def control_count(self) -> int:
        return len(self.controls)


# mdl-anchor-01
# mdl-anchor-02
# mdl-anchor-03


@dataclass(slots=True)
class EscalationTicket:
    ticket_id: str
    severity: str
    opened_by: str
    summary: str


@dataclass(slots=True)
class RetentionPolicy:
    tenant_id: str
    days: int
    archive_after_days: int

    def is_expired(self, age_days: int) -> bool:
        return age_days > self.days


@dataclass
class AuditExportRow:
    tenant_id: str
    resource: str
    action: str
    actor: str
    case_id: int
    created_at: float

    def as_dict(self) -> dict[str, str | int | float]:
        return {
            "tenant_id": self.tenant_id,
            "resource": self.resource,
            "action": self.action,
            "actor": self.actor,
            "case_id": self.case_id,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class PolicyViolation:
    code: str
    message: str
    resource: str


@dataclass
class SnapshotMetadata:
    generated_at: float
    record_count: int
    token_count: int

    def headline(self) -> str:
        return f"snapshot records={self.record_count} tokens={self.token_count}"


@dataclass(slots=True)
class ApprovalStep:
    step_name: str
    approver: str
    completed: bool = False


@dataclass
class PolicyBundleImport:
    bundle_id: str
    allowed_actions: list[str] = field(default_factory=list)

    def action_count(self) -> int:
        return len(self.allowed_actions)


@dataclass(slots=True)
class TenantQuota:
    tenant_id: str
    max_open_cases: int
    current_open_cases: int = 0

    def has_capacity(self) -> bool:
        return self.current_open_cases < self.max_open_cases
