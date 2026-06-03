"""验证 runtime_credentials 从 API 请求一路传递到所有 LLM 调用。"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.agents.llm_helpers import LLMRequiredError, _ensure_llm
from app.config import settings
from app.llm.credentials_resolve import (
    credentials_has_cloud,
    resolve_cloud_config,
    task_cloud_available,
)
from app.llm.openai_compat import OpenAICompatibleProvider, _sanitized_cloud_source
from app.llm.task_context import (
    TaskLLMContext,
    build_task_llm_context,
    clear_task_llm_context,
    set_task_llm_context,
)
from app.models.schemas import RuntimeCredentials


def _rt_creds(cloud_api_key: str = "sk-rt-key-123456") -> RuntimeCredentials:
    return RuntimeCredentials(cloud_api_key=cloud_api_key, cloud_flash_model="deepseek-chat")


# ── build_task_llm_context ────────────────────────────────────────────


class TestBuildTaskLLMContext:
    def test_runtime_credentials_provides_cloud_key(self):
        ctx = build_task_llm_context(
            llm_mode="cloud_only", runtime_credentials=_rt_creds()
        )
        assert ctx.cloud_api_key == "sk-rt-key-123456"

    def test_no_credentials_falls_back_to_settings(self, monkeypatch):
        # pydantic-settings 在 import 时缓存，需同时 patchenv 和 attr
        monkeypatch.setattr(settings, "deepseek_api_key", "pytest-key")
        monkeypatch.setattr(settings, "cloud_api_key", "")
        ctx = build_task_llm_context(llm_mode="cloud_only", runtime_credentials=None)
        assert ctx.cloud_api_key == "pytest-key"

    def test_runtime_key_priority_over_settings(self):
        ctx = build_task_llm_context(
            llm_mode="cloud_only", runtime_credentials=_rt_creds("sk-from-browser")
        )
        assert ctx.cloud_api_key == "sk-from-browser"


# ── _ensure_llm ───────────────────────────────────────────────────────


class TestEnsureLLM:
    def test_passes_with_runtime_credentials_when_settings_empty(self, monkeypatch):
        """settings 无 Key 但 runtime_credentials 有 Key → 不应报错。"""
        monkeypatch.setattr(settings, "cloud_api_key", "")
        monkeypatch.setattr(settings, "deepseek_api_key", "")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "")

        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_base="",
            cloud_api_key="",
        )
        set_task_llm_context(ctx)
        try:
            # settings 空，context 空，但传了 runtime_credentials → 应通过
            _ensure_llm(runtime_credentials=_rt_creds("sk-rt-123"))
        finally:
            clear_task_llm_context()

    def test_passes_with_task_context_key(self):
        """task context 已设置 Key → 即使不传 runtime_credentials 也应通过。"""
        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_base="https://api.deepseek.com",
            cloud_api_key="sk-from-ctx",
        )
        set_task_llm_context(ctx)
        try:
            _ensure_llm()  # 不传 runtime_credentials，靠 context
        finally:
            clear_task_llm_context()

    def test_raises_when_both_empty(self, monkeypatch):
        """settings 和 runtime_credentials 都空 → 必须抛出。"""
        monkeypatch.setattr(settings, "cloud_api_key", "")
        monkeypatch.setattr(settings, "deepseek_api_key", "")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "")

        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_base="",
            cloud_api_key="",
        )
        set_task_llm_context(ctx)
        try:
            with pytest.raises(LLMRequiredError):
                _ensure_llm(runtime_credentials=None)
        finally:
            clear_task_llm_context()


# ── credentials_resolve ───────────────────────────────────────────────


class TestResolveCloudConfig:
    def test_returns_config_from_runtime_credentials(self):
        resolved = resolve_cloud_config(_rt_creds("sk-browser"))
        assert resolved is not None
        assert resolved.api_key == "sk-browser"

    def test_returns_none_when_no_key_anywhere(self, monkeypatch):
        monkeypatch.setattr(settings, "cloud_api_key", "")
        monkeypatch.setattr(settings, "deepseek_api_key", "")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "")
        resolved = resolve_cloud_config(None)
        assert resolved is None

    def test_credentials_has_cloud_detects_key(self):
        assert credentials_has_cloud(_rt_creds("sk-xyz")) is True
        assert credentials_has_cloud(RuntimeCredentials()) is False
        assert credentials_has_cloud(None) is False

    def test_task_cloud_available_reads_context_key(self):
        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_key="sk-ctx-key",
        )
        assert task_cloud_available(ctx) is True

        ctx_empty = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_key="",
        )
        assert task_cloud_available(ctx_empty) is False


# ── OpenAICompatibleProvider ───────────────────────────────────────────


class TestOpenAIProviderKeySource:
    def test_resolve_from_task_uses_context_key(self):
        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_base="https://api.deepseek.com",
            cloud_api_key="sk-ctx-key-123",
        )
        set_task_llm_context(ctx)
        try:
            provider = OpenAICompatibleProvider()
            base, key = provider._resolve_from_task()
            assert key == "sk-ctx-key-123"
            assert "api.deepseek.com" in base
        finally:
            clear_task_llm_context()

    def test_resolve_from_task_falls_back_to_settings(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "pytest-key")
        monkeypatch.setattr(settings, "cloud_api_key", "")
        monkeypatch.setattr(settings, "deepseek_api_key", "pytest-key")
        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_key="",
            cloud_api_base="",
        )
        set_task_llm_context(ctx)
        try:
            provider = OpenAICompatibleProvider()
            _, key = provider._resolve_from_task()
            assert key == "pytest-key"
        finally:
            clear_task_llm_context()

    def test_headers_includes_bearer_token(self):
        ctx = TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="deepseek-chat",
            cloud_pro_model="",
            cloud_api_base="https://api.example.com",
            cloud_api_key="sk-headers-test",
        )
        set_task_llm_context(ctx)
        try:
            provider = OpenAICompatibleProvider()
            headers = provider._headers()
            assert headers["Authorization"] == "Bearer sk-headers-test"
        finally:
            clear_task_llm_context()


# ── 脱敏日志 ──────────────────────────────────────────────────────────


class TestSanitizedLogging:
    def test_source_is_runtime_when_context_has_key(self):
        source = _sanitized_cloud_source(
            base="https://api.example.com", key="", ctx_key="sk-12345678"
        )
        assert "runtime" in source
        assert "key_len=11" in source
        assert "sk-12345678" not in source

    def test_source_is_settings_when_ctx_empty(self):
        source = _sanitized_cloud_source(
            base="https://api.example.com", key="sk-settings-key", ctx_key=""
        )
        assert source == "settings"

    def test_source_is_none_when_both_empty(self):
        source = _sanitized_cloud_source(
            base="https://api.example.com", key="", ctx_key=""
        )
        assert source == "none"
