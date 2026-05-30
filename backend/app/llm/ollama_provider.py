from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider:
    """本地 Ollama HTTP API。"""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self._base = (base_url or settings.local_llm_base_url).rstrip("/")
        self._timeout = float(timeout_sec if timeout_sec is not None else settings.local_llm_timeout_sec)

    def available(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base}/api/tags")
                return resp.status_code == 200
        except Exception as e:
            logger.debug("Ollama 不可用: %s", e)
            return False

    def list_models(self) -> list[str]:
        if not self.available():
            return []
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            names: list[str] = []
            for item in data.get("models", []):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
            return sorted(set(names))
        except Exception as e:
            logger.warning("列举 Ollama 模型失败: %s", e)
            return []

    def complete_json_sync(self, *, model: str, system: str, user: str) -> dict[str, Any]:
        if not model.strip():
            raise RuntimeError("local_model_required")
        payload = {
            "model": model.strip(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{self._base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data.get("message", {}).get("content", "")
        return json.loads(content)

    def complete_text_sync(self, *, model: str, system: str, user: str) -> str:
        """压缩层用：纯文本输出，非 JSON。"""
        if not model.strip():
            raise RuntimeError("local_model_required")
        payload = {
            "model": model.strip(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{self._base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return str(data.get("message", {}).get("content", "")).strip()
