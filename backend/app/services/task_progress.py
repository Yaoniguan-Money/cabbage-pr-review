"""任务执行期间的 Agent 进度更新（供 graph 节点回调，避免与 task_runner 循环依赖）。"""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime

from app.services.task_store import task_store

_task_id_ctx: ContextVar[str | None] = ContextVar("task_progress_task_id", default=None)


def bind_task_progress(task_id: str) -> None:
    _task_id_ctx.set(task_id)


def clear_task_progress() -> None:
    _task_id_ctx.set(None)


def set_agent_status(agent_id: int, status: str, message: str = "") -> None:
    task_id = _task_id_ctx.get()
    if not task_id:
        return
    record = task_store.get(task_id)
    if not record:
        return
    for ap in record.agent_progress:
        if ap.agent_id == agent_id:
            ap.status = status  # type: ignore[assignment]
            ap.message = message
    record.current_agent = agent_id
    record.updated_at = datetime.utcnow()
    task_store.update(record)
