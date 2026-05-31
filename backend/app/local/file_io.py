from __future__ import annotations

import os
from pathlib import Path

ENTRY_HINTS = (
    "main.py",
    "app.py",
    "server.py",
    "index.ts",
    "index.tsx",
    "main.ts",
    "app.ts",
    "routes",
    "api",
)


def build_directory_tree(root: Path, max_depth: int = 4, max_entries: int = 200) -> list[str]:
    lines: list[str] = []
    if not root.exists():
        return lines

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth or len(lines) >= max_entries:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        for entry in entries:
            if entry.name.startswith(".") and entry.name not in (".env.example",):
                continue
            if entry.name in ("node_modules", "__pycache__", ".git", "dist", "build", "venv"):
                continue
            rel = str(entry.relative_to(root)).replace("\\", "/")
            lines.append(f"{prefix}{entry.name}/" if entry.is_dir() else f"{prefix}{entry.name}")
            if len(lines) >= max_entries:
                return
            if entry.is_dir():
                walk(entry, prefix + "  ", depth + 1)

    walk(root, "", 0)
    return lines


def find_entry_files(root: Path) -> list[str]:
    found: list[str] = []
    if not root.exists():
        return found
    for hint in ENTRY_HINTS:
        for p in root.rglob(hint if hint != "routes" else "routes"):
            if len(found) >= 30:
                return found
            rel = str(p.relative_to(root)).replace("\\", "/")
            if p.is_dir() or rel not in found:
                if not p.is_dir() or hint == "routes":
                    found.append(rel)
    return found[:30]


def read_readme(root: Path) -> str:
    for name in ("README.md", "readme.md", "Readme.md"):
        p = root / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")[:8000]
    return ""


def read_local_repo(path_str: str) -> dict:
    root = Path(path_str).resolve()
    if not root.is_dir():
        raise ValueError("本地路径不存在或不是目录")
    return {
        "root": str(root),
        "readme": read_readme(root),
        "tree": build_directory_tree(root),
        "entry_files": find_entry_files(root),
        "file_paths": [str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file()][:500],
    }


def count_patch_hunk_lines(patch_body: str) -> tuple[int, int]:
    """统计 unified diff 单文件 patch 的新增/删除行数。"""
    additions = deletions = 0
    for line in patch_body.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return additions, deletions


def parse_patch_text(patch: str) -> list[dict]:
    files: list[dict] = []
    current_file = ""
    current_patch: list[str] = []
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if current_file:
                body = "\n".join(current_patch)
                additions, deletions = count_patch_hunk_lines(body)
                files.append(
                    {
                        "filename": current_file,
                        "status": "modified",
                        "patch": body,
                        "additions": additions,
                        "deletions": deletions,
                    }
                )
            parts = line.split()
            if len(parts) >= 3:
                a_path = parts[2]
                current_file = a_path.removeprefix("a/").removeprefix("b/")
            current_patch = [line]
        else:
            current_patch.append(line)
    if current_file:
        body = "\n".join(current_patch)
        additions, deletions = count_patch_hunk_lines(body)
        files.append(
            {
                "filename": current_file,
                "status": "modified",
                "patch": body,
                "additions": additions,
                "deletions": deletions,
            }
        )
    if not files and patch.strip():
        additions, deletions = count_patch_hunk_lines(patch)
        files.append(
            {
                "filename": "unknown.patch",
                "status": "modified",
                "patch": patch,
                "additions": additions,
                "deletions": deletions,
            }
        )
    return files
