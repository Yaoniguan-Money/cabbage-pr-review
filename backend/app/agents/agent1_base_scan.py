from __future__ import annotations

from app.agents.base import extract_modules_from_paths, extract_routes_from_patches
from app.local.mermaid_render import diagram_from_modules, render_diagram
from app.models.schemas import ProjectIndexSchema


def run_agent1(pr_context: dict) -> ProjectIndexSchema:
    file_paths = pr_context.get("file_paths", [])
    patches = pr_context.get("patches", [])
    modules = extract_modules_from_paths(file_paths)
    routes = extract_routes_from_patches(patches)
    entry_files = [p for p in file_paths if any(h in p.lower() for h in ("main.py", "app.py", "index.ts", "server"))][:10]
    flow_hints = [
        f"PR 涉及 {pr_context.get('changed_files_count', len(file_paths))} 个文件",
        f"base 分支: {pr_context.get('base_ref', 'main')}",
    ]
    arch = diagram_from_modules("architecture", modules, routes)
    arch.mermaid = render_diagram(arch)
    return ProjectIndexSchema(
        modules=modules,
        routes=routes,
        entry_files=entry_files,
        flow_hints=flow_hints,
        architecture_diagram=arch,
        raw_summary=f"原版本索引：{len(modules)} 个模块，{len(routes)} 条路由线索",
    )
