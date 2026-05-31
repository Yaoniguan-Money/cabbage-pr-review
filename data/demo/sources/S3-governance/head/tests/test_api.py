"""REST API 层单元测试。"""
from __future__ import annotations

import pytest

from app.models import AuditRecord, PolicyDecision
from app.service import GovernanceService, ValidationError


@pytest.fixture
def service() -> GovernanceService:
    return GovernanceService()


@pytest.fixture
def sample_payload() -> dict[str, str]:
    return {
        "tenant_id": "acme-corp",
        "resource": "deployments/prod",
        "action": "approve",
        "actor": "reviewer@acme.example",
    }


def test_audit_record_case_01():
    assert GovernanceService().is_action_allowed("approve") is True  # case 1

def test_audit_record_case_02():
    assert GovernanceService().is_action_allowed("approve") is True  # case 2

def test_audit_record_case_03():
    assert GovernanceService().is_action_allowed("approve") is True  # case 3

def test_audit_record_case_18():
    assert GovernanceService().is_action_allowed("approve") is True  # case 18

# --- 中间保留块：策略缺省与参数化 ---

def test_policy_decision_defaults():
    assert PolicyDecision(allowed=True, reason="ok").allowed is True


def test_validate_missing_field_01(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_02(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_03(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_04(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_05(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_06(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_07(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

def test_validate_missing_field_18(service):
    with pytest.raises(ValidationError): service.validate_submission({}, required=("tenant_id",))

@pytest.mark.parametrize("action", ["approve", "escalate"])
def test_allowed_actions(service, action):
    assert service.is_action_allowed(action) is True


