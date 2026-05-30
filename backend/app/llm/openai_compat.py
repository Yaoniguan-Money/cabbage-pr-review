from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings

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
        self._timeout = timeout_sec

    def available(self) -> bool:
        return bool(self._api_key)

    def list_models(self) -> list[str]:
        return []

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _url(self) -> str:
        return f"{self._api_base}/chat/completions"

    def complete_json_sync(self, *, model: str, system: str, user: str) -> dict[str, Any]:
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
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
