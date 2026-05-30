from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.local.llm_mode import (
    HINT_CLOUD_UNAVAILABLE,
    HINT_COMPRESS_MODEL_REQUIRED,
    HINT_HYBRID_LOCAL_FOR_COMPRESS,
    VALID_LLM_MODES,
    get_availability_hints,
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
        "requires_llm",
        "quality_warning",
        "visualization_mode",
        "rerun_supported",
        "hide_token_stats",
        "default",
        "available",
        "unavailable_hint",
    }
)
_TOP_REQUIRED_KEYS = frozenset(
    {
        "options",
        "default_llm_mode",
        "default_local_compress_enabled",
        "default_rules_preflight_enabled",
        "cloud_available",
        "local_available",
        "local_models",
        "default_local_model",
        "availability_hints",
    }
)
_PREFLIGHT_TOGGLE_KEYS = frozenset({"default_enabled", "label", "hint_off"})
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
    assert len(data["options"]) == 4
    ids = {o["id"] for o in data["options"]}
    assert ids == VALID_LLM_MODES
    rules = next(o for o in data["options"] if o["id"] == "rules_only")
    assert rules["requires_llm"] is False
    assert rules["visualization_mode"] == "markdown"
    assert rules["rerun_supported"] is False
    assert rules["available"] is True
    hybrid = next(o for o in data["options"] if o["id"] == "hybrid")
    assert _OPTION_REQUIRED_KEYS <= set(hybrid.keys())
    assert hybrid["compress_toggle"] is not None
    assert _COMPRESS_TOGGLE_KEYS <= set(hybrid["compress_toggle"].keys())
    assert hybrid["rules_preflight_toggle"] is not None
    assert _PREFLIGHT_TOGGLE_KEYS <= set(hybrid["rules_preflight_toggle"].keys())
    cloud = next(o for o in data["options"] if o["id"] == "cloud_only")
    assert cloud["rules_preflight_toggle"] is not None
    assert hybrid["compress_toggle"]["default_enabled"] is True
    assert hybrid["available"] is False
    assert hybrid["unavailable_hint"] == HINT_HYBRID_LOCAL_FOR_COMPRESS
    local_only = next(o for o in data["options"] if o["id"] == "local_only")
    assert local_only["quality_warning"] is True
    assert local_only["available"] is False
    assert set(data["availability_hints"].keys()) == set(get_availability_hints().keys())


def test_hybrid_available_when_compress_off_without_local():
    data = list_llm_mode_options(
        default_mode="cloud_only",
        default_compress_enabled=False,
        cloud_available=True,
        local_available=False,
        local_models=[],
    )
    hybrid = next(o for o in data["options"] if o["id"] == "hybrid")
    assert hybrid["available"] is True
    assert hybrid["unavailable_hint"] is None
    local_only = next(o for o in data["options"] if o["id"] == "local_only")
    assert local_only["available"] is False


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


def test_validate_rules_only_skips_cloud():
    assert (
        validate_task_llm_config(
            llm_mode="rules_only",
            local_compress_enabled=False,
            local_model=None,
            cloud_available=False,
            local_available=False,
        )
        is None
    )


def test_validate_local_only_requires_model_and_local():
    from app.local.llm_mode import HINT_LOCAL_MODEL_REQUIRED, HINT_LOCAL_UNAVAILABLE

    assert (
        validate_task_llm_config(
            llm_mode="local_only",
            local_compress_enabled=False,
            local_model="",
            cloud_available=False,
            local_available=True,
        )
        == HINT_LOCAL_MODEL_REQUIRED
    )
    assert (
        validate_task_llm_config(
            llm_mode="local_only",
            local_compress_enabled=False,
            local_model="m",
            cloud_available=False,
            local_available=False,
        )
        == HINT_LOCAL_UNAVAILABLE
    )


def test_validate_hybrid_compress_off_skips_local():
    assert (
        validate_task_llm_config(
            llm_mode="hybrid",
            local_compress_enabled=False,
            local_model=None,
            cloud_available=True,
            local_available=False,
        )
        is None
    )


def test_llm_mode_options_api_contract():
    resp = client.get("/api/llm-mode-options")
    assert resp.status_code == 200
    body = resp.json()
    assert _TOP_REQUIRED_KEYS <= set(body.keys())
    assert body["default_llm_mode"] == settings.llm_mode
    assert set(body["availability_hints"].keys()) == set(get_availability_hints().keys())
    for opt in body["options"]:
        assert _OPTION_REQUIRED_KEYS <= set(opt.keys())
        assert "unavailable_hint" in opt
        if opt["id"] == "hybrid":
            assert opt.get("compress_toggle") is not None
            assert _COMPRESS_TOGGLE_KEYS <= set(opt["compress_toggle"].keys())
