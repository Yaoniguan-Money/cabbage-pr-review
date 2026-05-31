from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from app.config import settings
from app.local.llm_mode import normalize_llm_mode


@dataclass(frozen=True)
class TaskLLMContext:
    llm_mode: str
    local_compress_enabled: bool
    local_model: str
    cloud_flash_model: str
    cloud_pro_model: str


_task_llm_ctx: ContextVar[TaskLLMContext | None] = ContextVar("task_llm_ctx", default=None)


def build_task_llm_context(
    *,
    llm_mode: str | None = None,
    local_compress_enabled: bool | None = None,
    local_model: str | None = None,
    cloud_flash_model: str | None = None,
    cloud_pro_model: str | None = None,
) -> TaskLLMContext:
    mode = normalize_llm_mode(llm_mode, settings.llm_mode)
    compress = settings.local_compress_enabled if local_compress_enabled is None else local_compress_enabled
    if mode != "hybrid":
        compress = False
    return TaskLLMContext(
        llm_mode=mode,
        local_compress_enabled=compress,
        local_model=(local_model or settings.local_llm_default_model or "").strip(),
        cloud_flash_model=(cloud_flash_model or settings.cloud_flash_model_resolved).strip(),
        cloud_pro_model=(cloud_pro_model or settings.cloud_pro_model_resolved).strip(),
    )


def set_task_llm_context(ctx: TaskLLMContext) -> None:
    _task_llm_ctx.set(ctx)


def get_task_llm_context() -> TaskLLMContext:
    ctx = _task_llm_ctx.get()
    if ctx is not None:
        return ctx
    return build_task_llm_context()


def clear_task_llm_context() -> None:
    _task_llm_ctx.set(None)
