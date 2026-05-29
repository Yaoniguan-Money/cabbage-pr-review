from __future__ import annotations

from app.agents.base import extract_modules_from_paths, extract_routes_from_patches
from app.models.schemas import ProjectIndexSchema


def run_agent2(pr_context: dict) -> ProjectIndexSchema:
    file_paths = pr_context.get("file_paths", [])
    patches = pr_context.get("patches", [])
    modules = extract_modules_from_paths(file_paths)
    routes = extract_routes_from_patches(patches)
    entry_files = [p for p in file_paths if any(h in p.lower() for h in ("main.py", "app.py", "index.ts", "server"))][:10]
    return ProjectIndexSchema(
        modules=modules,
        routes=routes,
        entry_files=entry_files,
        flow_hints=[f"head 分支: {pr_context.get('head_ref', 'feature')}", f"PR 标题: {pr_context.get('title', '')[:80]}"],
        raw_summary=f"PR 后版本索引：{len(modules)} 个模块，{len(routes)} 条路由线索",
    )
