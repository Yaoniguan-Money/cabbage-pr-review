from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.local.llm_mode import (
    HINT_CLOUD_UNAVAILABLE,
    HINT_COMPRESS_MODEL_REQUIRED,
    VALID_LLM_MODES,
    list_llm_mode_options,
    normalize_llm_mode,
    validate_task_llm_config,
)
from app.main import app

client = TestClient(app)

# InputPage 依赖的 API 契约字段（不得在前端硬编码文案后仍缺字段）
_OPTION_REQUIRED_KEYS = frozenset(
    {
        "id",
        "label",
        "summary",
        "detail_bullets",
        "requires_cloud",
        "requires_local",
        "quality_warning",
        "default",
        "available",
    }
)
_TOP_REQUIRED_KEYS = frozenset(
    {
        "options",
        "default_llm_mode",
        "default_local_compress_enabled",
        "cloud_available",
        "local_available",
        "local_models",
        "default_local_model",
    }
)
_COMPRESS_TOGGLE_KEYS = frozenset({"default_enabled", "label", "hint_off"})


def test_normalize_llm_mode_fallback():
    assert normalize_llm_mode(None) == "cloud_only"
    assert normalize_llm_mode("invalid", "hybrid") == "hybrid"


def test_list_llm_mode_options_structure():
    data = list_llm_mode_options(
        default_mode="cloud_only",
        default_compress_enabled=True,
        cloud_available=True,
        local_available=False,
        local_models=[],
    )
    assert _TOP_REQUIRED_KEYS <= set(data.keys())
    assert len(data["options"]) == 3
    ids = {o["id"] for o in data["options"]}
    assert ids == VALID_LLM_MODES
    hybrid = next(o for o in data["options"] if o["id"] == "hybrid")
    assert _OPTION_REQUIRED_KEYS <= set(hybrid.keys())
    assert hybrid["compress_toggle"] is not None
    assert _COMPRESS_TOGGLE_KEYS <= set(hybrid["compress_toggle"].keys())
    assert hybrid["compress_toggle"]["default_enabled"] is True
    assert hybrid["available"] is False
    local_only = next(o for o in data["options"] if o["id"] == "local_only")
    assert local_only["quality_warning"] is True


def test_validate_task_llm_config_uses_hint_constants():
    assert (
        validate_task_llm_config(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model=None,
            cloud_available=False,
            local_available=False,
        )
        == HINT_CLOUD_UNAVAILABLE
    )
    assert (
        validate_task_llm_config(
            llm_mode="hybrid",
            local_compress_enabled=True,
            local_model="",
            cloud_available=True,
            local_available=True,
        )
        == HINT_COMPRESS_MODEL_REQUIRED
    )


def test_llm_mode_options_api_contract():
    resp = client.get("/api/llm-mode-options")
    assert resp.status_code == 200
    body = resp.json()
    assert _TOP_REQUIRED_KEYS <= set(body.keys())
    assert body["default_llm_mode"] == settings.llm_mode
    for opt in body["options"]:
        assert _OPTION_REQUIRED_KEYS <= set(opt.keys())
        if opt["id"] == "hybrid":
            assert opt.get("compress_toggle") is not None
            assert _COMPRESS_TOGGLE_KEYS <= set(opt["compress_toggle"].keys())
