from __future__ import annotations

import json

import httpx
import pytest

from app.llm.openai_compat import OpenAICompatibleProvider
from app.llm.token_usage import get_task_token_stats, reset_task_token_usage


def test_openai_compat_records_usage(monkeypatch: pytest.MonkeyPatch):
    reset_task_token_usage()

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": json.dumps({"ok": True})}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return FakeResp()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    provider = OpenAICompatibleProvider(api_key="test-key", api_base="https://example.com")
    out = provider.complete_json_sync(
        model="m",
        system="s",
        user="u",
        tier="flash",
    )
    assert out["ok"] is True
    stats = get_task_token_stats()
    assert stats is not None
    assert stats.cloud_prompt_tokens == 11
    assert stats.cloud_completion_tokens == 22
