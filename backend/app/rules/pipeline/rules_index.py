"""规则模式：结构索引（替代 Agent1/2）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from app.local.file_io import build_directory_tree, read_readme
from app.models.schemas import ProjectIndexSchema
from app.rules.rule_loader import load_index_hints, path_matches_glob


def _version_paths(patches: list[dict], version: Literal["base", "head"]) -> list[str]:
    if version == "base":
        statuses = {"modified", "removed", "renamed"}
    else:
        statuses = {"added", "modified", "renamed"}
    paths = [
        str(p.get("filename", "")).replace("\\", "/")
        for p in patches
        if p.get("filename") and (not p.get("status") or p.get("status") in statuses)
    ]
    return paths


def _find_entries(paths: list[str], hints: list[str]) -> list[str]:
    found: list[str] = []
    normalized_paths = [p.replace("\\", "/") for p in paths]
    for hint in hints:
        hint_lower = hint.lower()
        for path in normalized_paths:
            if hint_lower in path.lower() and path not in found:
                found.append(path)
                if len(found) >= 30:
                    return found
    return found


def _top_modules(paths: list[str]) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for path in paths:
        parts = path.replace("\\", "/").split("/")
        if not parts:
            continue
        top = parts[0]
        if top and top not in seen:
            seen.add(top)
            modules.append(top)
        if len(modules) >= 30:
            break
    return modules


def run_rules_index(
    pr_context: dict[str, Any],
    *,
    version: Literal["base", "head"],
) -> tuple[ProjectIndexSchema, list[str]]:
    notes: list[str] = []
    patches = pr_context.get("patches") or []
    file_paths = list(pr_context.get("file_paths") or [])
    version_paths = _version_paths(patches, version) or file_paths

    tree = list(pr_context.get("tree") or [])
    readme = str(pr_context.get("readme") or "")
    root = pr_context.get("local_root")

    if root and not tree:
        root_path = Path(str(root))
        tree = build_directory_tree(root_path)
        if not readme:
            readme = read_readme(root_path)

    hints = load_index_hints()
    entry_files = list(pr_context.get("entry_files") or [])
    if not entry_files:
        entry_files = _find_entries(version_paths or file_paths, hints)

    modules = _top_modules(version_paths or file_paths)
    summary = f"规则模式 {version} 索引：{len(version_paths)} 个相关路径"

    return (
        ProjectIndexSchema(
            version=version,
            modules=modules,
            routes=[p for p in version_paths if "route" in p.lower()][:20],
            entry_files=entry_files[:30],
            directory_tree=tree[:200],
            readme_excerpt=readme[:2000],
            raw_summary=summary,
        ),
        notes,
    )


def path_ignored(file_path: str, ignore_patterns: list[str]) -> bool:
    normalized = file_path.replace("\\", "/")
    return any(path_matches_glob(normalized, [pattern]) for pattern in ignore_patterns)
