"""Demo patch 体量统计（与 scripts/generate_demo_patches.py 校验口径一致）。"""

from __future__ import annotations

from typing import Any


def count_patch_stats(text: str) -> dict[str, Any]:
    plus = minus = 0
    per_file: dict[str, int] = {}
    current = ""
    hunk_files_multi = 0
    file_hunks: dict[str, int] = {}

    for line in text.splitlines():
        if line.startswith("diff --git"):
            parts = line.split(" b/")
            if len(parts) == 2:
                current = parts[1].strip()
                file_hunks.setdefault(current, 0)
            continue
        if line.startswith("@@") and current:
            file_hunks[current] = file_hunks.get(current, 0) + 1
            continue
        if not current:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            plus += 1
            per_file[current] = per_file.get(current, 0) + 1
        elif line.startswith("-") and not line.startswith("---"):
            minus += 1
            per_file[current] = per_file.get(current, 0) + 1

    for count in file_hunks.values():
        if count >= 2:
            hunk_files_multi += 1

    files_ge_15 = sum(1 for c in per_file.values() if c >= 15)
    return {
        "plus": plus,
        "minus": minus,
        "total": plus + minus,
        "files": len(per_file),
        "files_ge_15": files_ge_15,
        "multi_hunk_files": hunk_files_multi,
        "per_file": per_file,
        "file_paths": list(per_file.keys()),
    }


def assert_demo_patch_thresholds(text: str, *, label: str = "patch") -> dict[str, Any]:
    stats = count_patch_stats(text)
    assert stats["files"] >= 8, f"{label}: files {stats['files']}"
    assert stats["total"] >= 480, f"{label}: total {stats['total']}"
    assert stats["files_ge_15"] >= 6, f"{label}: files_ge_15 {stats['files_ge_15']}"
    assert stats["multi_hunk_files"] >= 2, f"{label}: multi_hunk {stats['multi_hunk_files']}"
    return stats
