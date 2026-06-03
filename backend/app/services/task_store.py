from __future__ import annotations

import threading
from typing import Callable

from app.models.schemas import TaskRecord


class TaskStore:
    """In-memory task store；允许多用户并发执行任务。"""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = threading.Lock()

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_all(self) -> list[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())

    async def create(self, record: TaskRecord) -> TaskRecord:
        record.init_agent_progress()
        with self._lock:
            self._tasks[record.id] = record
        return record

    async def run_exclusive(self, task_id: str, runner: Callable) -> None:
        """直接执行，不做全局单任务限制。多次调用可以在不同 task_id 上并发。"""
        await runner()

    def update(self, record: TaskRecord) -> None:
        with self._lock:
            self._tasks[record.id] = record


task_store = TaskStore()
