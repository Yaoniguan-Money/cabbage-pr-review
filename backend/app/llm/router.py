from __future__ import annotations

from typing import Any

from app.config import settings
from app.llm.credentials_resolve import cloud_available_for_request
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_compat import OpenAICompatibleProvider
from app.llm.task_context import TaskLLMContext, get_task_llm_context
from app.models.schemas import RuntimeCredentials

_cloud_provider = OpenAICompatibleProvider()
_local_provider = OllamaProvider()


def cloud_provider() -> OpenAICompatibleProvider:
    return _cloud_provider


def local_provider() -> OllamaProvider:
    return _local_provider


def cloud_available(
    *,
    runtime_credentials: RuntimeCredentials | None = None,
    has_runtime_cloud_key: bool = False,
) -> bool:
    return cloud_available_for_request(
        runtime_credentials,
        has_runtime_cloud_key=has_runtime_cloud_key,
    )


def local_available() -> bool:
    return _local_provider.available()


def list_local_models() -> list[str]:
    return _local_provider.list_models()


def complete_flash_json_sync(system: str, user: str, ctx: TaskLLMContext | None = None) -> dict[str, Any]:
    task_ctx = ctx or get_task_llm_context()
    model_cloud = task_ctx.cloud_flash_model or settings.cloud_flash_model_resolved
    if task_ctx.llm_mode == "local_only":
        return _local_provider.complete_json_sync(
            model=task_ctx.local_model,
            system=system,
            user=user,
            tier="local_flash",
        )
    return _cloud_provider.complete_json_sync(
        model=model_cloud, system=system, user=user, tier="flash"
    )


def complete_pro_json_sync(system: str, user: str, ctx: TaskLLMContext | None = None) -> dict[str, Any]:
    task_ctx = ctx or get_task_llm_context()
    model_cloud = task_ctx.cloud_pro_model or settings.cloud_pro_model_resolved
    if task_ctx.llm_mode == "local_only":
        return _local_provider.complete_json_sync(
            model=task_ctx.local_model,
            system=system,
            user=user,
            tier="local_pro",
        )
    return _cloud_provider.complete_json_sync(model=model_cloud, system=system, user=user, tier="pro")
