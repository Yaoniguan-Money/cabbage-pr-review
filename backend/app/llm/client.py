from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.local.llm_mode import normalize_llm_mode
from app.llm.router import complete_flash_json_sync, complete_pro_json_sync
from app.llm.task_context import get_task_llm_context

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """兼容层：委托 router，保留 conftest mock 挂载点。"""

    def _allow_call(self) -> bool:
        if settings.use_mock_llm:
            return False
        ctx = get_task_llm_context()
        if normalize_llm_mode(ctx.llm_mode, settings.llm_mode) == "local_only":
            return True
        if settings.llm_enabled:
            return True
        # 服务器未配置全局 Key 时，回退检查任务级 runtime_credentials
        from app.llm.credentials_resolve import task_cloud_available
        return task_cloud_available(ctx)

    def flash_json_sync(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        if not self._allow_call():
            raise RuntimeError("mock_only")
        return complete_flash_json_sync(system, user)

    def pro_json_sync(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        if not self._allow_call():
            raise RuntimeError("mock_only")
        return complete_pro_json_sync(system, user)

    async def flash_json(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return self.flash_json_sync(system, user, schema)

    async def pro_json(self, system: str, user: str, schema: type[T]) -> dict[str, Any]:
        return self.pro_json_sync(system, user, schema)


llm_client = LLMClient()
