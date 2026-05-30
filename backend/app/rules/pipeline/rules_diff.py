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


def _summarize_patch(patch_text: str) -> tuple[str, str, int, int]:
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
    return summary, excerpt, added, removed


def _split_patch_hunks(patch_text: str) -> list[str]:
    """按 unified diff @@ 块拆分为多个 hunk；无 @@ 时视为单块。"""
    if not patch_text.strip():
        return []
    hunks: list[str] = []
    current: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("@@"):
            if current:
                hunks.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        hunks.append("\n".join(current))
    if not hunks and patch_text.strip():
        return [patch_text]
    return hunks


def _append_atom(
    atoms: list[DiffAtom],
    *,
    atom_id: str,
    file_path: str,
    status: str,
    patch_text: str,
    hunk_index: int | None = None,
) -> None:
    summary, excerpt, added, removed = _summarize_patch(patch_text) if patch_text else ("文件级变更", "", 0, 0)
    symbol = f"hunk:{hunk_index}" if hunk_index is not None else ""
    if hunk_index is not None and summary.startswith("变更"):
        summary = f"hunk {hunk_index} · {summary}"
    atoms.append(
        DiffAtom(
            id=atom_id,
            file_path=file_path,
            change_type=status,  # type: ignore[arg-type]
            symbol=symbol,
            summary=summary,
            patch_excerpt=excerpt,
            hunk_patch=patch_text if hunk_index is not None else "",
            added_line_count=added,
            removed_line_count=removed,
        )
    )


def run_rules_diff(
    pr_context: dict[str, Any],
    *,
    ignore_patterns: list[str] | None = None,
    max_atoms: int = 200,
    split_patch_hunks: bool = True,
) -> tuple[DiffCompareSchema, list[str]]:
    notes: list[str] = []
    ignore = ignore_patterns or []
    patches = pr_context.get("patches") or []
    atoms: list[DiffAtom] = []
    atom_seq = 0

    for patch in patches:
        if len(atoms) >= max_atoms:
            notes.append(f"差异原子已达上限 {max_atoms}，后续文件未展开")
            break
        file_path = str(patch.get("filename") or f"file_{atom_seq}").replace("\\", "/")
        if path_ignored(file_path, ignore):
            continue
        status = _parse_status(str(patch.get("status") or "modified"))
        patch_text = str(patch.get("patch") or "")

        if not patch_text:
            atom_seq += 1
            _append_atom(
                atoms,
                atom_id=f"atom_{atom_seq}",
                file_path=file_path,
                status=status,
                patch_text="",
            )
            continue

        hunks = _split_patch_hunks(patch_text) if split_patch_hunks else [patch_text]
        use_hunk_atoms = split_patch_hunks and len(hunks) > 1

        if use_hunk_atoms:
            for hunk_idx, hunk_text in enumerate(hunks, start=1):
                if len(atoms) >= max_atoms:
                    notes.append(f"差异原子已达上限 {max_atoms}，后续 hunk 未展开")
                    break
                atom_seq += 1
                _append_atom(
                    atoms,
                    atom_id=f"atom_{atom_seq}",
                    file_path=file_path,
                    status=status,
                    patch_text=hunk_text,
                    hunk_index=hunk_idx,
                )
        else:
            atom_seq += 1
            _append_atom(
                atoms,
                atom_id=f"atom_{atom_seq}",
                file_path=file_path,
                status=status,
                patch_text=patch_text,
            )

    if not atoms and pr_context.get("file_paths"):
        for path in pr_context.get("file_paths") or []:
            if len(atoms) >= max_atoms:
                break
            file_path = str(path).replace("\\", "/")
            if path_ignored(file_path, ignore):
                continue
            atom_seq += 1
            atoms.append(
                DiffAtom(
                    id=f"atom_{atom_seq}",
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
