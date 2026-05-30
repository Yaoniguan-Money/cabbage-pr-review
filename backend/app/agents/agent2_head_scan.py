from __future__ import annotations

import json

from app.agents.llm_helpers import call_flash_json
from app.local.context_builder import build_version_scan_context
from app.models.schemas import ProjectIndexSchema


def run_agent2(pr_context: dict) -> tuple[ProjectIndexSchema, list[str]]:
    scan_ctx = build_version_scan_context(pr_context, version="head")
    if pr_context.get("head_tree"):
        scan_ctx["directory_tree"] = pr_context["head_tree"][:200]
    system = (
        "你是 Agent2 PR 后版本扫描。根据 README、目录树、入口文件与 head 版本源代码（code_snippets），"
        "输出完整 ProjectIndexSchema JSON，version 固定为 head。"
        "可选输出 architecture_diagram（nodes/edges，diagram_type=architecture），不要输出 mermaid。"
    )
    user = json.dumps(scan_ctx, ensure_ascii=False)
    result, notes = call_flash_json(system, user, ProjectIndexSchema)
    result.version = "head"
    return result, notes
