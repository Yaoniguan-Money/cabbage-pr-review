from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.local.llm_mode import (
    VALID_LLM_MODES,
    HINT_RERUN_NOT_SUPPORTED,
    format_llm_mode_label,
    get_llm_mode_option,
    is_rules_only_mode,
    normalize_llm_mode,
)
from app.local.review_depth import VALID_MODES, get_review_depth_option, normalize_review_depth_mode
from app.llm.task_context import build_task_llm_context
from app.models.schemas import CreateTaskRequest, InputType, RerunRequest, TaskRecord, TaskStatus
from app.services.export_md import export_markdown
from app.services.github import GitHubService
from app.services.llm_guard import ensure_llm_for_api
from app.services.task_runner import run_task_background
from app.services.task_store import task_store

router = APIRouter(prefix="/api", tags=["tasks"])


def _resolve_llm_fields(body: CreateTaskRequest) -> dict:
    llm_ctx = build_task_llm_context(
        llm_mode=body.llm_mode,
        local_compress_enabled=body.local_compress_enabled,
        local_model=body.local_model,
        cloud_flash_model=body.cloud_flash_model,
        cloud_pro_model=body.cloud_pro_model,
    )
    opt = get_llm_mode_option(llm_ctx.llm_mode, settings.llm_mode)
    rules_preflight_enabled = False
    if opt.rules_preflight_toggle is not None:
        if body.rules_preflight_enabled is not None:
            rules_preflight_enabled = body.rules_preflight_enabled
        else:
            rules_preflight_enabled = opt.rules_preflight_toggle.default_enabled
    return {
        "llm_mode": llm_ctx.llm_mode,
        "llm_mode_label": format_llm_mode_label(
            llm_ctx.llm_mode,
            local_compress_enabled=llm_ctx.local_compress_enabled,
            local_model=llm_ctx.local_model,
            fallback=settings.llm_mode,
        ),
        "visualization_mode": opt.visualization_mode,
        "rerun_supported": opt.rerun_supported,
        "local_compress_enabled": llm_ctx.local_compress_enabled,
        "local_model": llm_ctx.local_model,
        "cloud_flash_model": llm_ctx.cloud_flash_model,
        "cloud_pro_model": llm_ctx.cloud_pro_model,
        "rules_preflight_enabled": rules_preflight_enabled,
    }


@router.post("/tasks", response_model=TaskRecord)
async def create_task(body: CreateTaskRequest, background_tasks: BackgroundTasks):
    llm_fields = _resolve_llm_fields(body)
    if body.llm_mode and body.llm_mode not in VALID_LLM_MODES:
        raise HTTPException(status_code=400, detail="无效的推理模式")
    ensure_llm_for_api(
        llm_mode=llm_fields["llm_mode"],
        local_compress_enabled=llm_fields["local_compress_enabled"],
        local_model=llm_fields["local_model"] or None,
    )
    if body.input_type == InputType.PR_URL and not GitHubService.is_valid_pr_url(body.value):
        raise HTTPException(status_code=400, detail="无效的 GitHub PR URL")
    mode = normalize_review_depth_mode(body.review_depth_mode, settings.review_depth_mode)
    if body.review_depth_mode and body.review_depth_mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail="无效的审阅深度模式")
    depth_opt = get_review_depth_option(mode, settings.review_depth_mode)
    record = TaskRecord(
        input_type=body.input_type,
        input_value=body.value,
        project_type=body.project_type,
        framework=body.framework,
        review_depth_mode=mode,
        review_depth_label=depth_opt.label,
        **llm_fields,
    )
    await task_store.create(record)
    background_tasks.add_task(_start_task, record.id)
    return record


async def _start_task(task_id: str) -> None:
    record = task_store.get(task_id)
    if record:
        await run_task_background(record)


@router.get("/tasks/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str):
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="任务不存在")
    return record


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="任务不存在")
    if record.status != TaskStatus.COMPLETED or not record.result:
        raise HTTPException(status_code=409, detail="任务尚未完成")
    return record.result


@router.post("/tasks/{task_id}/rerun", response_model=TaskRecord)
async def rerun_task(task_id: str, body: RerunRequest, background_tasks: BackgroundTasks):
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="任务不存在")
    if is_rules_only_mode(record.llm_mode):
        raise HTTPException(status_code=400, detail=HINT_RERUN_NOT_SUPPORTED)
    ensure_llm_for_api(
        llm_mode=record.llm_mode,
        local_compress_enabled=record.local_compress_enabled,
        local_model=record.local_model or None,
    )
    if record.rerun_used:
        raise HTTPException(status_code=400, detail="已使用过补上下文重跑，仅允许一次")
    if record.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="请等待首次分析完成后再重跑")
    record.rerun_used = True
    record.rerun_context_paths = body.extra_context_paths
    record.rerun_focus_atoms = body.focus_atom_ids
    record.status = TaskStatus.PENDING
    record.init_agent_progress()
    task_store.update(record)

    async def _rerun():
        from app.services.task_runner import execute_task

        r = task_store.get(task_id)
        if not r:
            return

        async def runner() -> None:
            await execute_task(
                r,
                focus_atom_ids=body.focus_atom_ids,
                extra_context_paths=body.extra_context_paths,
            )

        await task_store.run_exclusive(task_id, runner)

    background_tasks.add_task(_rerun)
    return record


@router.get("/tasks/{task_id}/export.md", response_class=PlainTextResponse)
async def export_task_md(task_id: str):
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not record.result:
        raise HTTPException(status_code=409, detail="任务尚无结果可导出")
    content = export_markdown(record)
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
