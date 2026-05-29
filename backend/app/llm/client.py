from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

    def _url(self) -> str:
        return f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"

    def complete_json_sync(self, model: str, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        if settings.use_mock_llm or not settings.llm_enabled:
            raise RuntimeError("mock_only")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system + "\n请仅返回合法 JSON，不要 markdown 代码块。"},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(self._url(), json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    async def complete_json(self, model: str, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        if settings.use_mock_llm or not settings.llm_enabled:
            raise RuntimeError("mock_only")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system + "\n请仅返回合法 JSON，不要 markdown 代码块。"},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self._url(), json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    def flash_json_sync(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return self.complete_json_sync(settings.deepseek_flash_model, system, user, schema)

    def pro_json_sync(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return self.complete_json_sync(settings.deepseek_pro_model, system, user, schema)

    async def flash_json(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return await self.complete_json(settings.deepseek_flash_model, system, user, schema)

    async def pro_json(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return await self.complete_json(settings.deepseek_pro_model, system, user, schema)


llm_client = LLMClient()
