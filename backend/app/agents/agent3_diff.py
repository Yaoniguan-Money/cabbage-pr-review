from __future__ import annotations

import json

from app.agents.llm_helpers import call_flash_json
from app.local.diagram_utils import attach_mermaid
from app.models.schemas import DiffCompareSchema, ProjectIndexSchema


def run_agent3(
    base: ProjectIndexSchema, head: ProjectIndexSchema, pr_context: dict
) -> tuple[DiffCompareSchema, list[str]]:
    payload = {
        "base_index": base.model_dump(),
        "head_index": head.model_dump(),
        "patches": [
            {"filename": p.get("filename"), "status": p.get("status"), "patch": (p.get("patch") or "")[:4000]}
            for p in pr_context.get("patches", [])[:50]
        ],
    }
    system = (
        "你是 Agent3 差异对比 Agent。对比 base 与 head 的结构化索引及 patch 原文，"
        "输出 DiffCompareSchema：file_diffs、function_diffs、route_diffs、dependency_diffs、all_atoms，"
        "以及 impact_diagram（nodes/edges，diagram_type=impact_overlay）。不要输出 mermaid。"
    )
    user = json.dumps(payload, ensure_ascii=False)
    result, notes = call_flash_json(system, user, DiffCompareSchema)
    result.impact_diagram = attach_mermaid(result.impact_diagram)
    return result, notes
