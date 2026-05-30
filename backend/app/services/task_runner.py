from __future__ import annotations

from datetime import datetime

from app.graph.workflow import AGENT_NODE_ORDER, workflow_app
from app.llm.compress_context import (
    get_compress_degradation_notes,
    get_compress_stats,
    reset_compress_stats,
)
from app.models.schemas import CompressStatsSchema
from app.llm.task_context import build_task_llm_context, clear_task_llm_context, set_task_llm_context
from app.local.file_io import parse_patch_text, read_local_repo
from app.models.schemas import InputType, TaskRecord, TaskStatus
from app.services.github import github_service
from app.services.git_workspace import GitWorkspace, enrich_context_with_git
from app.services.task_store import task_store

NODE_TO_AGENT = {name: i + 1 for i, name in enumerate(AGENT_NODE_ORDER)}


async def _prepare_context(record: TaskRecord) -> tuple[dict, GitWorkspace | None]:
    if record.input_type == InputType.PR_URL:
        ctx = await github_service.fetch_pr_context(record.input_value)
    elif record.input_type == InputType.PATCH:
        patches = parse_patch_text(record.input_value)
        paths = [p["filename"] for p in patches]
        ctx = {
            "title": "Patch 分析",
            "file_paths": paths,
            "patches": patches,
            "changed_files_count": len(patches),
            "base_ref": "base",
            "head_ref": "head",
            "readme": "",
            "tree": sorted({p.split("/")[0] for p in paths if p}),
        }
    elif record.input_type == InputType.LOCAL_PATH:
        local = read_local_repo(record.input_value)
        ctx = {
            "title": f"本地仓库 {local['root']}",
            "local_root": local["root"],
            "file_paths": local["file_paths"],
            "patches": [{"filename": p, "status": "modified", "patch": ""} for p in local["file_paths"][:30]],
            "changed_files_count": len(local["file_paths"]),
            "readme": local.get("readme", ""),
            "tree": local.get("tree", []),
            "entry_files": local.get("entry_files", []),
            "base_ref": "local",
            "head_ref": "local",
        }
    else:
        raise ValueError("不支持的输入类型")

    ctx, git_ws = await enrich_context_with_git(ctx)
    return ctx, git_ws


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
    for ap in record.agent_progress:
        ap.status = "pending"
        ap.message = ""
    task_store.update(record)

    git_ws: GitWorkspace | None = None
    llm_ctx = build_task_llm_context(
        llm_mode=record.llm_mode,
        local_compress_enabled=record.local_compress_enabled,
        local_model=record.local_model or None,
        cloud_flash_model=record.cloud_flash_model or None,
        cloud_pro_model=record.cloud_pro_model or None,
    )
    set_task_llm_context(llm_ctx)
    reset_compress_stats()
    try:
        pr_context, git_ws = await _prepare_context(record)
        record.pr_context = pr_context
        task_store.update(record)

        state = {
            "pr_context": pr_context,
            "git_ws": git_ws,
            "project_type": record.project_type,
            "framework": record.framework,
            "focus_atom_ids": focus_atom_ids or record.rerun_focus_atoms or [],
            "extra_context_paths": extra_context_paths or record.rerun_context_paths or [],
            "review_depth_mode": record.review_depth_mode,
            "degradation_notes": [],
        }

        final_state = dict(state)
        async for event in workflow_app.astream(state):
            for node_name, update in event.items():
                agent_id = NODE_TO_AGENT.get(node_name, 0)
                if agent_id:
                    _set_agent_status(record, agent_id, "running")
                if isinstance(update, dict):
                    final_state.update(update)
                    if final_state.get("degradation_notes"):
                        record.pr_context["degradation_notes"] = final_state["degradation_notes"]
                if agent_id:
                    _set_agent_status(record, agent_id, "completed")

        compress_notes = get_compress_degradation_notes()
        if compress_notes:
            merged = list(compress_notes) + list(final_state.get("degradation_notes") or [])
            final_state["degradation_notes"] = merged
            record.pr_context["degradation_notes"] = merged

        stats = get_compress_stats()
        if stats.compress_calls > 0 or stats.chars_before > 0:
            record.compress_stats = CompressStatsSchema(
                compress_calls=stats.compress_calls,
                chars_before=stats.chars_before,
                chars_after=stats.chars_after,
            )

        result = final_state.get("final_result")
        if result and final_state.get("degradation_notes"):
            result.degradation_notes = list(final_state["degradation_notes"]) + list(result.degradation_notes)
        record.result = result
        record.status = TaskStatus.COMPLETED
    except Exception as e:
        record.status = TaskStatus.FAILED
        record.error_message = str(e)
        if record.current_agent:
            _set_agent_status(record, record.current_agent, "failed", str(e))
    finally:
        if git_ws:
            git_ws.cleanup()
        clear_task_llm_context()
    record.updated_at = datetime.utcnow()
    task_store.update(record)


async def run_task_background(record: TaskRecord) -> None:
    async def _runner() -> None:
        await execute_task(record)

    await task_store.run_exclusive(record.id, _runner)
