from __future__ import annotations

from pathlib import Path
from typing import Any

from app.local.file_io import build_directory_tree, find_entry_files, read_readme
from app.local.text_preprocess import truncate
from app.llm.compress_context import compress_file_map


def _changed_paths_from_patches(patches: list[dict]) -> set[str]:
    return {str(p.get("filename", "")).replace("\\", "/") for p in patches if p.get("filename")}


def build_version_scan_context(pr_context: dict[str, Any], *, version: str) -> dict[str, Any]:
    """构建 Agent1(base) / Agent2(head) 扫描上下文。"""
    patches = pr_context.get("patches", [])
    file_paths = list(pr_context.get("file_paths", []))
    readme = pr_context.get("readme", "")
    tree_key = "base_tree" if version == "base" else "head_tree"
    tree = list(pr_context.get(tree_key) or pr_context.get("tree", []))
    entry_files = list(pr_context.get("entry_files", []))
    root = pr_context.get("local_root")

    contents_key = "base_file_contents" if version == "base" else "head_file_contents"
    file_contents: dict[str, str] = dict(pr_context.get(contents_key, {}))

    if version == "base":
        version_paths = [
            p["filename"]
            for p in patches
            if p.get("status") in ("modified", "removed", "renamed")
        ] or file_paths
    else:
        version_paths = [
            p["filename"]
            for p in patches
            if p.get("status") in ("added", "modified", "renamed")
        ] or file_paths

    if not file_contents and patches and not pr_context.get("git_workspace_attached"):
        file_contents = _patch_text_only(patches, head=(version == "head"))

    if root and not tree:
        root_path = Path(root)
        tree = build_directory_tree(root_path)
        entry_files = find_entry_files(root_path) or entry_files
        if not readme:
            readme = read_readme(root_path)

    if not entry_files:
        entry_files = [
            p
            for p in version_paths
            if any(h in p.lower() for h in ("main.py", "app.py", "index.ts", "index.tsx", "server"))
        ][:15]

    entry_set = {p.replace("\\", "/") for p in entry_files}
    changed = _changed_paths_from_patches(patches)
    file_contents = compress_file_map(
        file_contents,
        changed_paths=changed,
        entry_files=entry_set,
    )

    return {
        "version": version,
        "readme": truncate(readme, 8000),
        "directory_tree": tree[:200],
        "entry_files": entry_files[:30],
        "file_paths": version_paths[:500],
        "code_snippets": file_contents,
        "title": pr_context.get("title", ""),
        "ref": pr_context.get("base_ref" if version == "base" else "head_ref", ""),
    }


def _patch_text_only(patches: list[dict], *, head: bool) -> dict[str, str]:
    """无 git 仓库时：仅传递 patch 原文供 LLM 分析（数据输入，非业务判定）。"""
    out: dict[str, str] = {}
    for p in patches:
        fn = p.get("filename", "")
        patch = p.get("patch") or ""
        if not patch:
            continue
        lines: list[str] = []
        for line in patch.splitlines():
            if head and line.startswith("+") and not line.startswith("+++"):
                lines.append(line)
            elif not head and line.startswith("-") and not line.startswith("---"):
                lines.append(line)
        if lines:
            out[fn] = truncate("\n".join(lines), 8000)
        elif patch:
            out[fn] = truncate(patch, 8000)
    return out


def load_extra_context_files(
    pr_context: dict[str, Any],
    extra_paths: list[str],
    git_ws: Any | None = None,
) -> dict[str, str]:
    loaded: dict[str, str] = {}
    root = pr_context.get("local_root")
    head_sha = pr_context.get("head_sha")

    for raw in extra_paths[:10]:
        path_str = raw.strip().replace("\\", "/")
        if not path_str:
            continue
        if git_ws and head_sha and hasattr(git_ws, "read_files_at_ref"):
            loaded.update(git_ws.read_files_at_ref([path_str], head_sha))
            continue
        path = Path(path_str)
        if not path.is_absolute() and root:
            path = Path(root) / path_str
        if path.is_file():
            loaded[path_str] = truncate(path.read_text(encoding="utf-8", errors="ignore"), 12000)
        elif path.is_dir() and path.exists():
            for child in list(path.rglob("*.py"))[:5] + list(path.rglob("*.ts"))[:5]:
                rel = str(child.relative_to(path)).replace("\\", "/")
                loaded[rel] = truncate(child.read_text(encoding="utf-8", errors="ignore"), 12000)
    patches = pr_context.get("patches", [])
    entry_files = {str(p).replace("\\", "/") for p in pr_context.get("entry_files", [])}
    return compress_file_map(
        loaded,
        changed_paths=_changed_paths_from_patches(patches),
        entry_files=entry_files,
    )


async def load_extra_context_files_async(
    pr_context: dict[str, Any],
    extra_paths: list[str],
    git_ws: Any | None = None,
) -> dict[str, str]:
    loaded: dict[str, str] = {}
    root = pr_context.get("local_root")
    head_sha = pr_context.get("head_sha")

    for raw in extra_paths[:10]:
        path_str = raw.strip().replace("\\", "/")
        if not path_str:
            continue
        if git_ws and head_sha:
            got = git_ws.read_files_at_ref([path_str], head_sha)
            loaded.update(got)
            continue
        path = Path(path_str)
        if not path.is_absolute() and root:
            path = Path(root) / path_str
        if path.is_file():
            loaded[path_str] = truncate(path.read_text(encoding="utf-8", errors="ignore"), 12000)
        elif path.is_dir() and path.exists():
            for child in list(path.rglob("*.py"))[:5] + list(path.rglob("*.ts"))[:5]:
                rel = str(child.relative_to(path)).replace("\\", "/")
                loaded[rel] = truncate(child.read_text(encoding="utf-8", errors="ignore"), 12000)
    patches = pr_context.get("patches", [])
    entry_files = {str(p).replace("\\", "/") for p in pr_context.get("entry_files", [])}
    return compress_file_map(
        loaded,
        changed_paths=_changed_paths_from_patches(patches),
        entry_files=entry_files,
    )
