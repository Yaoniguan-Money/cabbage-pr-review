from __future__ import annotations

from datetime import datetime

from app.graph.workflow import workflow_app
from app.local.file_io import parse_patch_text, read_local_repo
from app.models.schemas import InputType, TaskRecord, TaskStatus
from app.services.github import github_service
from app.services.task_store import task_store


async def _prepare_context(record: TaskRecord) -> dict:
    if record.input_type == InputType.PR_URL:
        return await github_service.fetch_pr_context(record.input_value)
    if record.input_type == InputType.PATCH:
        patches = parse_patch_text(record.input_value)
        paths = [p["filename"] for p in patches]
        return {
            "title": "Patch 分析",
            "file_paths": paths,
            "patches": patches,
            "changed_files_count": len(patches),
            "base_ref": "base",
            "head_ref": "head",
        }
    if record.input_type == InputType.LOCAL_PATH:
        local = read_local_repo(record.input_value)
        return {
            "title": f"本地仓库 {local['root']}",
            "file_paths": local["file_paths"],
            "patches": [{"filename": p, "status": "modified", "patch": ""} for p in local["file_paths"][:30]],
            "changed_files_count": len(local["file_paths"]),
            "readme": local.get("readme", ""),
            "tree": local.get("tree", []),
            "entry_files": local.get("entry_files", []),
            "base_ref": "local",
            "head_ref": "local",
        }
    raise ValueError("不支持的输入类型")


def _set_agent_status(record: TaskRecord, agent_id: int, status: str, message: str = "") -> None:
    for ap in record.agent_progress:
        if ap.agent_id == agent_id:
            ap.status = status
            ap.message = message
    record.current_agent = agent_id
    record.updated_at = datetime.utcnow()
    task_store.update(record)


async def execute_task(
    record: TaskRecord,
    *,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
) -> None:
    record.status = TaskStatus.RUNNING
    record.error_message = None
    task_store.update(record)

    try:
        pr_context = await _prepare_context(record)
        record.pr_context = pr_context
        task_store.update(record)

        state = {
            "pr_context": pr_context,
            "project_type": record.project_type,
            "framework": record.framework,
            "focus_atom_ids": focus_atom_ids or record.rerun_focus_atoms or [],
            "extra_context_paths": extra_context_paths or record.rerun_context_paths or [],
            "degradation_notes": [],
        }

        for i in range(1, 6):
            _set_agent_status(record, i, "running")

        final_state = await workflow_app.ainvoke(state)

        for i in range(1, 6):
            _set_agent_status(record, i, "completed")

        record.result = final_state.get("final_result")
        record.status = TaskStatus.COMPLETED
    except Exception as e:
        record.status = TaskStatus.FAILED
        record.error_message = str(e)
        if record.current_agent:
            _set_agent_status(record, record.current_agent, "failed", str(e))
    record.updated_at = datetime.utcnow()
    task_store.update(record)


async def run_task_background(record: TaskRecord) -> None:
    async def _runner() -> None:
        await execute_task(record)

    await task_store.run_exclusive(record.id, _runner)
