"""规则模式：patch 解析为 DiffAtom（替代 Agent3）。"""

from __future__ import annotations

from typing import Any

from app.models.schemas import DiffAtom, DiffCompareSchema
from app.rules.pipeline.rules_index import path_ignored


def _parse_status(raw: str) -> str:
    value = (raw or "modified").lower()
    if value in {"added", "modified", "removed", "renamed"}:
        return value
    return "modified"


def _summarize_patch(patch_text: str) -> tuple[str, str]:
    added = removed = 0
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    excerpt_lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            excerpt_lines.append(line[1:][:120])
        if len(excerpt_lines) >= 8:
            break
    excerpt = "\n".join(excerpt_lines)[:500]
    summary = f"变更 +{added}/-{removed} 行"
    return summary, excerpt


def run_rules_diff(
    pr_context: dict[str, Any],
    *,
    ignore_patterns: list[str] | None = None,
    max_atoms: int = 200,
) -> tuple[DiffCompareSchema, list[str]]:
    notes: list[str] = []
    ignore = ignore_patterns or []
    patches = pr_context.get("patches") or []
    atoms: list[DiffAtom] = []

    for idx, patch in enumerate(patches):
        if len(atoms) >= max_atoms:
            notes.append(f"差异原子已达上限 {max_atoms}，后续文件未展开")
            break
        file_path = str(patch.get("filename") or f"file_{idx}").replace("\\", "/")
        if path_ignored(file_path, ignore):
            continue
        status = _parse_status(str(patch.get("status") or "modified"))
        patch_text = str(patch.get("patch") or "")
        summary, excerpt = _summarize_patch(patch_text) if patch_text else ("文件级变更", "")

        atom_id = f"atom_{idx + 1}"
        atoms.append(
            DiffAtom(
                id=atom_id,
                file_path=file_path,
                change_type=status,  # type: ignore[arg-type]
                symbol="",
                summary=summary,
                patch_excerpt=excerpt,
            )
        )

    if not atoms and pr_context.get("file_paths"):
        for idx, path in enumerate(pr_context.get("file_paths") or []):
            if len(atoms) >= max_atoms:
                break
            file_path = str(path).replace("\\", "/")
            if path_ignored(file_path, ignore):
                continue
            atoms.append(
                DiffAtom(
                    id=f"atom_{idx + 1}",
                    file_path=file_path,
                    change_type="modified",
                    summary="文件出现在变更列表中",
                )
            )

    diff = DiffCompareSchema(
        file_diffs=atoms,
        all_atoms=atoms,
    )
    return diff, notes
