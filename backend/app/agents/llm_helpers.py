from __future__ import annotations

import logging
from typing import Any
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.llm.client import llm_client
from app.local.result_repair import repair_model

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMRequiredError(RuntimeError):
    """未配置 DeepSeek 或显式禁用 LLM 时抛出。"""


def _ensure_llm() -> None:
    if settings.use_mock_llm or not settings.llm_enabled:
        raise LLMRequiredError(
            "分析需要 DeepSeek API：请在 .env 配置 DEEPSEEK_API_KEY 且 USE_MOCK_LLM=false"
        )


def call_flash_json(system: str, user: str, schema: type[T]) -> tuple[T, list[str]]:
    _ensure_llm()
    notes: list[str] = []
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            raw = llm_client.flash_json_sync(system, user, schema)
            raw_data: dict[str, Any] = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)
            return repair_model(schema, raw_data), notes
        except (ValidationError, Exception) as e:
            last_err = e
            logger.warning("Flash JSON 校验/调用失败 attempt=%s: %s", attempt + 1, e)
            notes.append(f"Flash 重试 {attempt + 1}: {e}")
    raise RuntimeError(f"DeepSeek Flash 在 2 次尝试后仍失败: {last_err}") from last_err


def call_pro_json(system: str, user: str, schema: type[T]) -> tuple[T, list[str]]:
    _ensure_llm()
    notes: list[str] = []
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            raw = llm_client.pro_json_sync(system, user, schema)
            raw_data: dict[str, Any] = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)
            return repair_model(schema, raw_data), notes
        except (ValidationError, Exception) as e:
            last_err = e
            logger.warning("Pro JSON 校验/调用失败 attempt=%s: %s", attempt + 1, e)
            notes.append(f"Pro 重试 {attempt + 1}: {e}")
    raise RuntimeError(f"DeepSeek Pro 在 2 次尝试后仍失败: {last_err}") from last_err
