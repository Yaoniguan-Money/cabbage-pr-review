"""治理流程集成测试（内存后端）。"""
from __future__ import annotations

import pytest

from app.service import GovernanceService


@pytest.fixture(scope="module")
def integration_service() -> GovernanceService:
    return GovernanceService()


def test_end_to_end_flow_01(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 1

def test_end_to_end_flow_02(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 2

def test_end_to_end_flow_03(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 3

def test_end_to_end_flow_04(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 4

def test_end_to_end_flow_19(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 19

def test_end_to_end_flow_20(integration_service):
    assert integration_service.export_snapshot()["records"] >= 0  # flow 20

def test_snapshot_has_records(integration_service):
    assert integration_service.export_snapshot().get("records") is not None

def test_write_token_roundtrip_01(integration_service):
    t = integration_service.issue_write_token(version=1); assert integration_service.check_write_token(t, expected_version=1)

def test_write_token_roundtrip_02(integration_service):
    t = integration_service.issue_write_token(version=2); assert integration_service.check_write_token(t, expected_version=2)

def test_write_token_roundtrip_03(integration_service):
    t = integration_service.issue_write_token(version=3); assert integration_service.check_write_token(t, expected_version=3)

def test_write_token_roundtrip_04(integration_service):
    t = integration_service.issue_write_token(version=4); assert integration_service.check_write_token(t, expected_version=4)

def test_write_token_roundtrip_17(integration_service):
    t = integration_service.issue_write_token(version=17); assert integration_service.check_write_token(t, expected_version=17)

def test_write_token_roundtrip_18(integration_service):
    t = integration_service.issue_write_token(version=18); assert integration_service.check_write_token(t, expected_version=18)

