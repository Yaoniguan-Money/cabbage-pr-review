"""任务级运行时凭据暂存（内存，不落盘，任务结束后清除）。"""

from __future__ import annotations

from app.models.schemas import RuntimeCredentials

_store: dict[str, RuntimeCredentials] = {}


def stash_task_credentials(task_id: str, creds: RuntimeCredentials | None) -> None:
    if creds is None or not credentials_present(creds):
        return
    _store[task_id] = creds


def pop_task_credentials(task_id: str) -> RuntimeCredentials | None:
    return _store.pop(task_id, None)


def credentials_present(creds: RuntimeCredentials) -> bool:
    return bool(
        (creds.cloud_api_key or "").strip()
        or (creds.github_token or "").strip()
        or (creds.cloud_api_base or "").strip()
    )
