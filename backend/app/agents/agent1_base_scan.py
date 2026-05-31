from __future__ import annotations

import json

from app.agents.llm_helpers import call_flash_json
from app.local.context_builder import build_version_scan_context
from app.models.schemas import ProjectIndexSchema


def run_agent1(pr_context: dict) -> tuple[ProjectIndexSchema, list[str]]:
    scan_ctx = build_version_scan_context(pr_context, version="base")
    if pr_context.get("base_tree"):
        scan_ctx["directory_tree"] = pr_context["base_tree"][:200]
    system = (
        "你是 Agent1 原版本扫描。根据 README、目录树、入口文件与 base 版本源代码（code_snippets），"
        "输出完整 ProjectIndexSchema JSON。必须包含 architecture_diagram（nodes/edges，diagram_type=architecture），"
        "version 固定为 base。不要输出 mermaid 字段。"
    )
    user = json.dumps(scan_ctx, ensure_ascii=False)
    result, notes = call_flash_json(system, user, ProjectIndexSchema)
    result.version = "base"
    return result, notes
