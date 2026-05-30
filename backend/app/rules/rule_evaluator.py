"""规则求值：对 patch / 路径 / diff atom 执行 YAML 中声明的 pattern。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.schemas import DiffAtom
from app.rules.rule_loader import file_in_rule_scope, language_allowed
from app.rules.rule_schema import RuleDefinition, RuleHitRecord, RuleMatchClause


@dataclass
class RuleContext:
    pr_title: str = ""
    pr_body: str = ""
    modified_files: list[str] = field(default_factory=list)
    patches_by_file: dict[str, str] = field(default_factory=dict)
    added_lines_by_file: dict[str, list[str]] = field(default_factory=dict)


def build_rule_context(pr_context: dict) -> RuleContext:
    patches = pr_context.get("patches") or []
    patches_by_file: dict[str, str] = {}
    added_lines: dict[str, list[str]] = {}
    modified: list[str] = []

    for patch in patches:
        filename = str(patch.get("filename") or "").replace("\\", "/")
        if not filename:
            continue
        modified.append(filename)
        text = str(patch.get("patch") or "")
        patches_by_file[filename] = text
        added_lines[filename] = _extract_added_lines(text)

    if not modified:
        modified = [str(p).replace("\\", "/") for p in pr_context.get("file_paths") or []]

    return RuleContext(
        pr_title=str(pr_context.get("title") or ""),
        pr_body=str(pr_context.get("body") or pr_context.get("description") or ""),
        modified_files=modified,
        patches_by_file=patches_by_file,
        added_lines_by_file=added_lines,
    )


def _extract_added_lines(patch_text: str) -> list[str]:
    lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return lines


def _compile_pattern(pattern: str) -> re.Pattern[str] | None:
    if not pattern.strip():
        return None
    try:
        return re.compile(pattern, re.MULTILINE)
    except re.error:
        return None


def _match_text(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    snippet = match.group(0)
    return snippet[:500] if len(snippet) > 500 else snippet


def _evaluate_clause(
    clause: RuleMatchClause,
    *,
    file_path: str,
    atom: DiffAtom,
    ctx: RuleContext,
) -> str | None:
    pattern = _compile_pattern(clause.pattern_regex)
    if pattern is None:
        return None

    target = clause.target
    if target == "file_path":
        return _match_text(pattern, file_path)

    if target == "diff_atom":
        blob = "\n".join(
            part for part in (atom.file_path, atom.symbol, atom.summary, atom.patch_excerpt) if part
        )
        return _match_text(pattern, blob)

    # patch_hunk：优先新增行，其次完整 patch
    added = "\n".join(ctx.added_lines_by_file.get(file_path, []))
    if added and _match_text(pattern, added):
        return _match_text(pattern, added)
    patch = ctx.patches_by_file.get(file_path, atom.patch_excerpt)
    return _match_text(pattern, patch)


def _clauses_match(
    clauses: list[RuleMatchClause],
    *,
    file_path: str,
    atom: DiffAtom,
    ctx: RuleContext,
    require_all: bool,
) -> str | None:
    if not clauses:
        return None
    evidences: list[str] = []
    for clause in clauses:
        hit = _evaluate_clause(clause, file_path=file_path, atom=atom, ctx=ctx)
        if require_all:
            if hit is None:
                return None
            evidences.append(hit)
        elif hit is not None:
            return hit
    if require_all and evidences:
        return evidences[0]
    return None


def evaluate_rule_on_atom(
    rule: RuleDefinition,
    atom: DiffAtom,
    ctx: RuleContext,
) -> RuleHitRecord | None:
    file_path = atom.file_path.replace("\\", "/")
    if not file_in_rule_scope(file_path, rule):
        return None
    if not language_allowed(file_path, rule.languages):
        return None

    evidence: str | None = None
    if rule.match.all:
        evidence = _clauses_match(
            rule.match.all, file_path=file_path, atom=atom, ctx=ctx, require_all=True
        )
    if evidence is None and rule.match.any:
        evidence = _clauses_match(
            rule.match.any, file_path=file_path, atom=atom, ctx=ctx, require_all=False
        )
    if evidence is None:
        return None

    return RuleHitRecord(
        rule_id=rule.id,
        severity=rule.severity,
        file_path=file_path,
        evidence=evidence,
        message=rule.message,
    )
