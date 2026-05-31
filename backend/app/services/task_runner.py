from __future__ import annotations

from datetime import datetime

from app.graph.state import AgentOutcomeValue, GraphState
from app.graph.workflow import AGENT_NODE_ORDER, workflow_app
from app.local.file_io import parse_patch_text, read_local_repo
from app.models.schemas import InputType, TaskOutcome, TaskRecord, TaskStatus
from app.services.github import github_service
from app.services.git_workspace import GitWorkspace, enrich_context_with_git
from app.services.task_store import task_store

NODE_TO_AGENT = {name: i + 1 for i, name in enumerate(AGENT_NODE_ORDER)}
CRITICAL_AGENTS = (3, 4, 5)


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


def _dedupe_notes(notes: list[str]) -> list[str]:
    out: list[str] = []
    for note in notes:
        if note and note not in out:
            out.append(note)
    return out


def _agent_progress_status(outcome: AgentOutcomeValue) -> str:
    return {"ok": "completed", "degraded": "degraded", "failed": "failed"}[outcome]


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


async def execute_task(
    record: TaskRecord,
    *,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
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
    try:
        pr_context, git_ws = await _prepare_context(record)
        record.pr_context = pr_context
        task_store.update(record)

        state: GraphState = {
            "pr_context": pr_context,
            "git_ws": git_ws,
            "project_type": record.project_type,
            "framework": record.framework,
            "focus_atom_ids": focus_atom_ids or record.rerun_focus_atoms or [],
            "extra_context_paths": extra_context_paths or record.rerun_context_paths or [],
            "degradation_notes": [],
            "agent_outcomes": {},
            "agent_errors": {},
        }

        final_state: GraphState = dict(state)
        async for event in workflow_app.astream(state):
            for node_name, update in event.items():
                agent_id = NODE_TO_AGENT.get(node_name, 0)
                if agent_id:
                    _set_agent_status(record, agent_id, "running")
                if isinstance(update, dict):
                    final_state.update(update)
                    if final_state.get("degradation_notes"):
                        notes = _dedupe_notes(list(final_state["degradation_notes"]))
                        record.pr_context["degradation_notes"] = notes
                        record.degradation_notes = notes
                if agent_id:
                    outcome = (final_state.get("agent_outcomes", {}) or {}).get(agent_id, "ok")
                    message = (final_state.get("agent_errors", {}) or {}).get(agent_id, "")
                    _set_agent_status(record, agent_id, _agent_progress_status(outcome), message)

        result = final_state.get("final_result")
        if result:
            result.degradation_notes = _dedupe_notes(
                list(final_state.get("degradation_notes", [])) + list(result.degradation_notes)
            )

        record.degradation_notes = _dedupe_notes(list(final_state.get("degradation_notes", [])))
        record.status, record.outcome, record.error_message = _derive_task_completion(final_state)
        if record.status == TaskStatus.COMPLETED:
            record.result = result
        else:
            record.result = None
    except Exception as e:
        record.status = TaskStatus.FAILED
        record.outcome = TaskOutcome.FAILED
        record.error_message = str(e)
        if record.current_agent:
            _set_agent_status(record, record.current_agent, "failed", str(e))
    finally:
        if git_ws:
            git_ws.cleanup()
    record.updated_at = datetime.utcnow()
    task_store.update(record)


async def run_task_background(record: TaskRecord) -> None:
    async def _runner() -> None:
        await execute_task(record)

    await task_store.run_exclusive(record.id, _runner)
