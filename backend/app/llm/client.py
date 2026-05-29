from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
  async def complete_json(self, model: str, system: str, user: str, schema: type[T]) -> T:
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
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"}
    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=120.0) as client:
      resp = await client.post(url, json=payload, headers=headers)
      resp.raise_for_status()
      data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return schema.model_validate(parsed)

  async def flash_json(self, system: str, user: str, schema: type[T]) -> T:
    return await self.complete_json(settings.deepseek_flash_model, system, user, schema)

  async def pro_json(self, system: str, user: str, schema: type[T]) -> T:
    return await self.complete_json(settings.deepseek_pro_model, system, user, schema)


llm_client = LLMClient()
