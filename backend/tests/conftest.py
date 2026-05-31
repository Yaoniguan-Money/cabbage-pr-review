from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.models.schemas import (
    AtomContextPlanBatch,
    AtomPriorityBatch,
    DiffCompareSchema,
    ProjectIndexSchema,
    RiskReviewSchema,
    VisualizationSchema,
)

FIXTURES = Path(__file__).parent / "fixtures"

os.environ.setdefault("DEEPSEEK_API_KEY", "pytest-key")
os.environ.setdefault("USE_MOCK_LLM", "false")
os.environ.setdefault("LLM_MODE", "cloud_only")


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _mock_flash(_system: str, _user: str, schema: type):
    name = schema.__name__
    if name == "ProjectIndexSchema":
        data = _load_json("project_index.json")
        if '"version": "head"' in _user or '"version": "head"' in _user.replace(" ", ""):
            data = {**data, "version": "head", "raw_summary": "head 索引"}
        return ProjectIndexSchema.model_validate(data)
    if name == "DiffCompareSchema":
        return DiffCompareSchema.model_validate(_load_json("diff_compare.json"))
    if name == "AtomPriorityBatch":
        return AtomPriorityBatch.model_validate(_load_json("atom_priority.json"))
    if name == "VisualizationSchema":
        return VisualizationSchema.model_validate(_load_json("visualization.json"))
    raise ValueError(f"未准备的 Flash schema: {name}")


def _mock_pro(_system: str, _user: str, schema: type):
    name = schema.__name__
    if name == "AtomContextPlanBatch":
        return AtomContextPlanBatch.model_validate(_load_json("atom_plan_batch.json"))
    if name == "RiskReviewSchema":
        return RiskReviewSchema.model_validate(_load_json("risk_review.json"))
    raise ValueError(f"未准备的 Pro schema: {name}")


@pytest.fixture(autouse=True)
def patch_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.llm.client.llm_client.flash_json_sync", _mock_flash)
    monkeypatch.setattr("app.llm.client.llm_client.pro_json_sync", _mock_pro)
