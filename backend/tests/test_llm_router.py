from __future__ import annotations

import pytest

from app.llm.router import complete_flash_json_sync, complete_pro_json_sync
from app.llm.task_context import TaskLLMContext, set_task_llm_context, clear_task_llm_context


@pytest.fixture(autouse=True)
def _clear_ctx():
    clear_task_llm_context()
    yield
    clear_task_llm_context()


def test_cloud_only_uses_cloud_provider(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_cloud(*, model: str, system: str, user: str):
        calls.append(f"cloud:{model}")
        return {"ok": True}

    monkeypatch.setattr("app.llm.router._cloud_provider.complete_json_sync", fake_cloud)
    set_task_llm_context(
        TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=False,
            local_model="",
            cloud_flash_model="flash-test",
            cloud_pro_model="pro-test",
        )
    )
    complete_flash_json_sync("s", "u")
    complete_pro_json_sync("s", "u")
    assert calls == ["cloud:flash-test", "cloud:pro-test"]


def test_local_only_uses_local_provider(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_local(*, model: str, system: str, user: str):
        calls.append(f"local:{model}")
        return {"ok": True}

    monkeypatch.setattr("app.llm.router._local_provider.complete_json_sync", fake_local)
    set_task_llm_context(
        TaskLLMContext(
            llm_mode="local_only",
            local_compress_enabled=False,
            local_model="my-local",
            cloud_flash_model="flash-test",
            cloud_pro_model="pro-test",
        )
    )
    complete_flash_json_sync("s", "u")
    complete_pro_json_sync("s", "u")
    assert calls == ["local:my-local", "local:my-local"]
