from __future__ import annotations

from datetime import datetime

from app.graph.state import AgentOutcomeValue, GraphState
from app.graph.workflow import workflow_app
from app.graph.workflow_helpers import dedupe_notes
from app.llm.compress_context import (
    get_compress_degradation_notes,
    get_compress_stats,
    reset_compress_stats,
)
from app.llm.task_context import build_task_llm_context, clear_task_llm_context, set_task_llm_context
from app.llm.token_usage import get_task_token_stats, reset_task_token_usage
from app.local.demo_patches_meta import merge_demo_context_overlay
from app.local.file_io import parse_patch_text, read_local_repo
from app.local.workflow_meta import WORKFLOW_NODE_AGENT_MAP
from app.models.schemas import CompressStatsSchema, InputType, RuntimeCredentials, TaskOutcome, TaskRecord, TaskStatus
from app.services.github import github_service
from app.services.git_workspace import GitWorkspace, enrich_context_with_git, redact_git_secrets
from app.services import task_progress
from app.services.task_store import task_store

NODE_TO_AGENTS = WORKFLOW_NODE_AGENT_MAP
CRITICAL_AGENTS = (3, 4, 5)


async def _prepare_context(
    record: TaskRecord,
    *,
    github_token: str = "",
) -> tuple[dict, GitWorkspace | None]:
    if record.input_type == InputType.PR_URL:
        ctx = await github_service.fetch_pr_context(record.input_value, github_token=github_token or None)
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

    ctx, git_ws = await enrich_context_with_git(ctx, github_token=github_token)
    if record.demo_scenario_id:
        ctx = merge_demo_context_overlay(ctx, record.demo_scenario_id)
    return ctx, git_ws


def _set_agent_status(record: TaskRecord, agent_id: int, status: str, message: str = "") -> None:
    for ap in record.agent_progress:
        if ap.agent_id == agent_id:
            ap.status = status  # type: ignore[assignment]
            ap.message = message
    record.current_agent = agent_id
    record.updated_at = datetime.utcnow()
    task_store.update(record)


def _agent_progress_status(outcome: AgentOutcomeValue) -> str:
    return {"ok": "completed", "degraded": "degraded", "failed": "failed"}[outcome]


def _set_agents_running(record: TaskRecord, agent_ids: list[int]) -> None:
    for aid in agent_ids:
        _set_agent_status(record, aid, "running")


def _sync_agent_progress_from_outcomes(
    record: TaskRecord,
    agent_ids: list[int],
    final_state: GraphState,
) -> None:
    outcomes = final_state.get("agent_outcomes", {}) or {}
    errors = final_state.get("agent_errors", {}) or {}
    for aid in agent_ids:
        if aid in outcomes:
            message = errors.get(aid, "")
            _set_agent_status(record, aid, _agent_progress_status(outcomes[aid]), message)
        else:
            for ap in record.agent_progress:
                if ap.agent_id == aid and ap.status == "running":
                    _set_agent_status(record, aid, "degraded", "agent outcome missing")


def _derive_task_completion(state: GraphState) -> tuple[TaskStatus, TaskOutcome, str | None]:
    result = state.get("final_result")
    outcomes = state.get("agent_outcomes", {})
    errors = state.get("agent_errors", {})
    failures: list[str] = []

    if not result:
        failures.append("FAILED/task_runner: workflow produced no final_result")
    elif not result.summary.strip():
        failures.append("FAILED/task_runner: final_result.summary is empty")

    for agent_id in CRITICAL_AGENTS:
        if outcomes.get(agent_id) == "failed":
            failures.append(errors.get(agent_id) or f"FAILED/Agent{agent_id}: critical agent failed")

    if failures:
        return TaskStatus.FAILED, TaskOutcome.FAILED, failures[0]

    if any(outcome == "degraded" for outcome in outcomes.values()) or state.get("degradation_notes"):
        return TaskStatus.COMPLETED, TaskOutcome.DEGRADED, None

    return TaskStatus.COMPLETED, TaskOutcome.OK, None


def _log_task_key_setup(task_id: str, llm_ctx, runtime_credentials) -> None:
    import logging

    _logger = logging.getLogger(__name__)
    has_rt = runtime_credentials is not None
    rt_key_len = (
        len((runtime_credentials.cloud_api_key or "").strip()) if has_rt else 0
    )
    ctx_key_len = len(llm_ctx.cloud_api_key.strip())
    source = "runtime" if ctx_key_len > 0 else ("settings" if rt_key_len > 0 else "none")
    _logger.info(
        "task_llm_context task_id=%s has_runtime_credentials=%s runtime_cloud_key_len=%s "
        "resolved_cloud_key_len=%s resolved_cloud_key_source=%s",
        task_id, has_rt, rt_key_len, ctx_key_len, source,
    )


async def execute_task(
    record: TaskRecord,
    *,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
    runtime_credentials: RuntimeCredentials | None = None,
) -> None:
    record.status = TaskStatus.RUNNING
    record.outcome = None
    record.error_message = None
    record.result = None
    record.current_agent = 0
    record.degradation_notes = []
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
        runtime_credentials=runtime_credentials,
    )
    set_task_llm_context(llm_ctx)
    # 脱敏日志：记录任务级 key 来源
    _log_task_key_setup(record.id, llm_ctx, runtime_credentials)
    gh_token = llm_ctx.github_token
    reset_compress_stats()
    reset_task_token_usage()
    task_progress.bind_task_progress(record.id)
    try:
        pr_context, git_ws = await _prepare_context(record, github_token=gh_token)
        fetch_warnings = pr_context.pop("fetch_warnings", None)
        if fetch_warnings:
            pr_context["degradation_notes"] = dedupe_notes(
                list(pr_context.get("degradation_notes") or []) + list(fetch_warnings)
            )
        record.pr_context = pr_context
        if fetch_warnings:
            record.degradation_notes = dedupe_notes(list(record.degradation_notes) + list(fetch_warnings))
        task_store.update(record)

        state: GraphState = {
            "pr_context": pr_context,
            "git_ws": git_ws,
            "project_type": record.project_type,
            "framework": record.framework,
            "focus_atom_ids": focus_atom_ids or record.rerun_focus_atoms or [],
            "extra_context_paths": extra_context_paths or record.rerun_context_paths or [],
            "review_depth_mode": record.review_depth_mode,
            "llm_mode": record.llm_mode,
            "degradation_notes": [],
            "agent_outcomes": {},
            "agent_errors": {},
            "rule_hits": [],
        }

        final_state: GraphState = dict(state)
        async for event in workflow_app.astream(state):
            for node_name, update in event.items():
                agent_ids = NODE_TO_AGENTS.get(node_name, [])
                if agent_ids:
                    _set_agents_running(record, agent_ids)
                if isinstance(update, dict):
                    final_state.update(update)
                    if final_state.get("degradation_notes"):
                        notes = dedupe_notes(list(final_state["degradation_notes"]))
                        record.pr_context["degradation_notes"] = notes
                        record.degradation_notes = notes
                if agent_ids:
                    _sync_agent_progress_from_outcomes(record, agent_ids, final_state)

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

        record.token_stats = get_task_token_stats()

        result = final_state.get("final_result")
        if result:
            result.degradation_notes = dedupe_notes(
                list(final_state.get("degradation_notes", [])) + list(result.degradation_notes)
            )

        record.degradation_notes = dedupe_notes(list(final_state.get("degradation_notes", [])))
        record.status, record.outcome, record.error_message = _derive_task_completion(final_state)
        if record.status == TaskStatus.COMPLETED:
            record.result = result
        else:
            record.result = None
    except Exception as e:
        record.status = TaskStatus.FAILED
        record.outcome = TaskOutcome.FAILED
        record.error_message = redact_git_secrets(str(e), gh_token)
        if record.current_agent:
            _set_agent_status(record, record.current_agent, "failed", str(e))
        record.token_stats = get_task_token_stats()
    finally:
        task_progress.clear_task_progress()
        if git_ws:
            git_ws.cleanup()
        clear_task_llm_context()
    record.updated_at = datetime.utcnow()
    task_store.update(record)


async def run_task_background(
    record: TaskRecord,
    *,
    runtime_credentials: RuntimeCredentials | None = None,
) -> None:
    async def _runner() -> None:
        await execute_task(record, runtime_credentials=runtime_credentials)

    await task_store.run_exclusive(record.id, _runner)
