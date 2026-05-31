"""规则求值：对 patch / 路径 / diff atom 执行 YAML 中声明的 pattern。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.schemas import DiffAtom
from app.rules.rule_loader import file_in_rule_scope, language_allowed
from app.rules.rule_ast import run_ast_query
from app.rules.rule_pattern import compile_pattern
from app.rules.rule_schema import RuleDefinition, RuleHitRecord, RuleMatchClause, RulePackReporting

_METADATA_THRESHOLD_KEYS = (
    "min_added_lines",
    "min_removed_lines",
    "min_changed_lines",
    "min_removed_ratio",
    "min_removed_over_added",
    "requires_removed_signal",
)


@dataclass
class RuleContext:
    pr_title: str = ""
    pr_body: str = ""
    modified_files: list[str] = field(default_factory=list)
    patches_by_file: dict[str, str] = field(default_factory=dict)
    added_lines_by_file: dict[str, list[str]] = field(default_factory=dict)
    removed_lines_by_file: dict[str, list[str]] = field(default_factory=dict)


def build_rule_context(pr_context: dict) -> RuleContext:
    patches = pr_context.get("patches") or []
    patches_by_file: dict[str, str] = {}
    added_lines: dict[str, list[str]] = {}
    removed_lines: dict[str, list[str]] = {}
    modified: list[str] = []

    for patch in patches:
        filename = str(patch.get("filename") or "").replace("\\", "/")
        if not filename:
            continue
        modified.append(filename)
        text = str(patch.get("patch") or "")
        patches_by_file[filename] = text
        added_lines[filename] = _extract_added_lines(text)
        removed_lines[filename] = _extract_removed_lines(text)

    if not modified:
        modified = [str(p).replace("\\", "/") for p in pr_context.get("file_paths") or []]

    return RuleContext(
        pr_title=str(pr_context.get("title") or ""),
        pr_body=str(pr_context.get("body") or pr_context.get("description") or ""),
        modified_files=modified,
        patches_by_file=patches_by_file,
        added_lines_by_file=added_lines,
        removed_lines_by_file=removed_lines,
    )


def _extract_added_lines(patch_text: str) -> list[str]:
    lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return lines


def _extract_removed_lines(patch_text: str) -> list[str]:
    lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            lines.append(line[1:])
    return lines


def _match_text(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    snippet = match.group(0)
    return snippet[:500] if len(snippet) > 500 else snippet


def _patch_scope_text(
    *,
    file_path: str,
    atom: DiffAtom,
    ctx: RuleContext,
    scope: str,
) -> str:
    """按 patch_scope 取匹配文本；hunk 级 atom 优先使用 hunk_patch。"""
    if atom.hunk_patch:
        if scope == "removed_only":
            return "\n".join(_extract_removed_lines(atom.hunk_patch))
        if scope == "full_patch":
            return atom.hunk_patch
        return "\n".join(_extract_added_lines(atom.hunk_patch))

    if scope == "removed_only":
        return "\n".join(ctx.removed_lines_by_file.get(file_path, []))
    if scope == "full_patch":
        return ctx.patches_by_file.get(file_path, atom.patch_excerpt)
    return "\n".join(ctx.added_lines_by_file.get(file_path, []))


def _patch_hunk_text(
    *,
    file_path: str,
    atom: DiffAtom,
    ctx: RuleContext,
    scope: str,
) -> str:
    return _patch_scope_text(file_path=file_path, atom=atom, ctx=ctx, scope=scope)


def _evaluate_clause(
    clause: RuleMatchClause,
    *,
    file_path: str,
    atom: DiffAtom,
    ctx: RuleContext,
) -> str | None:
    if clause.matcher_type == "ast":
        if not clause.ast_query.strip():
            return None
        hunk_text = _patch_hunk_text(
            file_path=file_path, atom=atom, ctx=ctx, scope=clause.patch_scope
        )
        return run_ast_query(
            file_path=file_path,
            source=hunk_text,
            query_text=clause.ast_query,
            ast_filter=clause.ast_filter,
        )

    pattern = compile_pattern(clause.pattern_regex)
    if pattern is None:
        return None

    target = clause.target
    if target == "file_path":
        return _match_text(pattern, file_path)

    if target == "change_type":
        return _match_text(pattern, atom.change_type)

    if target == "pr_title":
        return _match_text(pattern, ctx.pr_title)

    if target == "pr_body":
        return _match_text(pattern, ctx.pr_body)

    if target == "removed_lines":
        removed = "\n".join(ctx.removed_lines_by_file.get(file_path, []))
        if removed:
            return _match_text(pattern, removed)
        return _match_text(pattern, ctx.patches_by_file.get(file_path, atom.patch_excerpt))

    if target == "diff_atom":
        blob = "\n".join(
            part
            for part in (
                atom.file_path,
                atom.symbol,
                atom.summary,
                atom.patch_excerpt,
                str(atom.added_line_count),
                str(atom.removed_line_count),
            )
            if part
        )
        return _match_text(pattern, blob)

    # patch_hunk：按 patch_scope 选择匹配文本
    hunk_text = _patch_hunk_text(
        file_path=file_path, atom=atom, ctx=ctx, scope=clause.patch_scope
    )
    if hunk_text and _match_text(pattern, hunk_text):
        return _match_text(pattern, hunk_text)
    if clause.patch_scope == "added_only":
        if atom.hunk_patch:
            patch = atom.hunk_patch
        else:
            patch = ctx.patches_by_file.get(file_path, atom.patch_excerpt)
        return _match_text(pattern, patch)
    return None


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


def _metadata_thresholds_met(rule: RuleDefinition, atom: DiffAtom) -> tuple[bool, str]:
    meta = rule.metadata
    threshold_keys = (
        "min_added_lines",
        "min_removed_lines",
        "min_changed_lines",
        "min_removed_ratio",
        "min_removed_over_added",
        "requires_removed_signal",
    )
    if not any(key in meta for key in threshold_keys):
        return True, ""

    added = atom.added_line_count
    removed = atom.removed_line_count
    changed = added + removed

    if meta.get("requires_removed_signal") and removed == 0:
        return False, ""

    if "min_added_lines" in meta and added < int(meta["min_added_lines"]):
        return False, ""
    if "min_removed_lines" in meta and removed < int(meta["min_removed_lines"]):
        return False, ""
    if "min_changed_lines" in meta and changed < int(meta["min_changed_lines"]):
        return False, ""

    if "min_removed_ratio" in meta:
        denom = changed
        if denom == 0:
            return False, ""
        ratio = removed / denom
        if ratio < float(meta["min_removed_ratio"]):
            return False, ""

    if "min_removed_over_added" in meta:
        required = added * float(meta["min_removed_over_added"])
        if removed < required:
            return False, ""

    return True, f"变更 +{added}/-{removed} 行"


def enrich_hit_evidence(
    *,
    raw_evidence: str,
    atom: DiffAtom,
    rule: RuleDefinition,
    reporting: RulePackReporting,
) -> str:
    """通用证据拼装：atom.summary 与 regex 片段，由包级/规则级 metadata 控制。"""
    include_summary = bool(rule.metadata.get("evidence_include_summary"))
    if not include_summary:
        include_summary = reporting.evidence_include_atom_summary

    parts: list[str] = []
    if include_summary and (atom.summary or "").strip():
        parts.append(atom.summary.strip())
    snippet = (raw_evidence or "").strip()
    if snippet:
        parts.append(snippet)
    if not parts:
        return raw_evidence[:500] if raw_evidence else ""
    joined = " | ".join(parts)
    return joined[:500]


def evaluate_rule_on_atom(
    rule: RuleDefinition,
    atom: DiffAtom,
    ctx: RuleContext,
    *,
    reporting: RulePackReporting | None = None,
) -> RuleHitRecord | None:
    file_path = atom.file_path.replace("\\", "/")
    if not file_in_rule_scope(file_path, rule):
        return None
    if not language_allowed(file_path, rule.languages):
        return None

    threshold_ok, threshold_evidence = _metadata_thresholds_met(rule, atom)
    if not threshold_ok:
        return None

    has_threshold = any(key in rule.metadata for key in _METADATA_THRESHOLD_KEYS)

    evidence: str | None = None
    if rule.match.all:
        evidence = _clauses_match(
            rule.match.all, file_path=file_path, atom=atom, ctx=ctx, require_all=True
        )
    if evidence is None and rule.match.any:
        evidence = _clauses_match(
            rule.match.any, file_path=file_path, atom=atom, ctx=ctx, require_all=False
        )
    has_explicit_match = bool(rule.match.all or rule.match.any)
    if evidence is None and has_threshold and not has_explicit_match:
        evidence = threshold_evidence
    if evidence is None:
        return None

    pack_reporting = reporting or RulePackReporting()
    final_evidence = enrich_hit_evidence(
        raw_evidence=evidence,
        atom=atom,
        rule=rule,
        reporting=pack_reporting,
    )

    return RuleHitRecord(
        rule_id=rule.id,
        severity=rule.severity,
        file_path=file_path,
        evidence=final_evidence,
        message=rule.message,
    )
