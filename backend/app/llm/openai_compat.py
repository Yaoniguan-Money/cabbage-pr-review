from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.llm.credentials_resolve import resolve_cloud_config
from app.llm.task_context import get_task_llm_context
from app.llm.token_usage import parse_openai_usage, record_token_usage

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:
    """任意 OpenAI 兼容 chat/completions 云端后端。"""

    def __init__(
        self,
        *,
        api_base: str | None = None,
        api_key: str | None = None,
        timeout_sec: float = 120.0,
    ) -> None:
        self._api_base = (api_base or settings.cloud_api_base_resolved).rstrip("/")
        self._api_key = (api_key or settings.cloud_api_key_resolved).strip()
        self._timeout = timeout_sec if timeout_sec != 120.0 else settings.cloud_timeout_sec

    def _resolve_from_task(self) -> tuple[str, str]:
        ctx = get_task_llm_context()
        if ctx.cloud_api_key.strip():
            return ctx.cloud_api_base.rstrip("/"), ctx.cloud_api_key.strip()
        resolved = resolve_cloud_config(None)
        if resolved:
            return resolved.api_base.rstrip("/"), resolved.api_key
        return self._api_base, self._api_key

    def available(self) -> bool:
        _, key = self._resolve_from_task()
        return bool(key)

    def list_models(self) -> list[str]:
        return []

    def _headers(self) -> dict[str, str]:
        _, key = self._resolve_from_task()
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _url(self) -> str:
        base, _ = self._resolve_from_task()
        return f"{base}/chat/completions"

    def complete_json_sync(
        self,
        *,
        model: str,
        system: str,
        user: str,
        tier: str | None = None,
    ) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError("cloud_unavailable")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system + "\n请仅返回合法 JSON，不要 markdown 代码块。"},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(self._url(), json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        if tier:
            usage = data.get("usage")
            prompt, completion, estimated = parse_openai_usage(usage if isinstance(usage, dict) else None)
            if not usage:
                logger.debug("云端响应无 usage 字段，tier=%s", tier)
            record_token_usage(
                tier=tier,
                prompt_tokens=prompt,
                completion_tokens=completion,
                estimated=estimated,
            )
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
