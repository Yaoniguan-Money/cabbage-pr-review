from __future__ import annotations

import asyncio
from typing import Callable

from app.models.schemas import TaskOutcome, TaskRecord, TaskStatus


class TaskStore:
    """In-memory task store with single-runner execution semantics."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()
        self._running: str | None = None

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[TaskRecord]:
        return list(self._tasks.values())

    async def create(self, record: TaskRecord) -> TaskRecord:
        record.init_agent_progress()
        self._tasks[record.id] = record
        return record

    async def run_exclusive(self, task_id: str, runner: Callable) -> None:
        async with self._lock:
            if self._running and self._running != task_id:
                task = self._tasks[task_id]
                task.status = TaskStatus.FAILED
                task.outcome = TaskOutcome.FAILED
                task.error_message = "另有分析任务正在执行，请等待完成后再试"
                return
            self._running = task_id
        try:
            await runner()
        finally:
            async with self._lock:
                if self._running == task_id:
                    self._running = None

    def update(self, record: TaskRecord) -> None:
        self._tasks[record.id] = record


task_store = TaskStore()
