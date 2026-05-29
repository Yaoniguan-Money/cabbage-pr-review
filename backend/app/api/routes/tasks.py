from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse

from app.models.schemas import CreateTaskRequest, InputType, RerunRequest, TaskRecord, TaskStatus
from app.services.export_md import export_markdown
from app.services.github import GitHubService
from app.services.task_runner import run_task_background
from app.services.task_store import task_store

router = APIRouter(prefix="/api", tags=["tasks"])


@router.post("/tasks", response_model=TaskRecord)
async def create_task(body: CreateTaskRequest, background_tasks: BackgroundTasks):
    if body.input_type == InputType.PR_URL and not GitHubService.is_valid_pr_url(body.value):
        raise HTTPException(status_code=400, detail="无效的 GitHub PR URL")
    record = TaskRecord(
        input_type=body.input_type,
        input_value=body.value,
        project_type=body.project_type,
        framework=body.framework,
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
