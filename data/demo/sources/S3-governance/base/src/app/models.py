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
