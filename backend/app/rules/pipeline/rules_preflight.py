"""LLM 模式可选规则预检：通用编排，业务规则仍在 YAML。"""

from __future__ import annotations

from app.models.schemas import DiffCompareSchema
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_schema import RuleHitRecord


def format_rule_hits_for_prompt(hits: list[RuleHitRecord], *, limit: int = 50) -> list[dict[str, str]]:
    """将规则命中格式化为可注入 LLM prompt 的结构化片段。"""
    rows: list[dict[str, str]] = []
    for hit in hits[:limit]:
        rows.append(
            {
                "rule_id": hit.rule_id,
                "severity": hit.severity,
                "file_path": hit.file_path,
                "message": hit.message,
                "evidence": hit.evidence[:300],
            }
        )
    return rows


def run_rules_preflight(
    diff: DiffCompareSchema,
    pr_context: dict,
    *,
    review_depth_mode: str = "balanced",
) -> tuple[list[RuleHitRecord], list[str]]:
    """对 LLM diff 结果运行 YAML 规则求值，返回命中与说明。"""
    _, hits, _, notes = run_rules_review(diff, pr_context, review_depth_mode=review_depth_mode)
    if hits:
        notes.append(f"规则预检命中 {len(hits)} 次，已注入 Agent4 上下文")
    return hits, notes
