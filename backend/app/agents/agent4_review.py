from __future__ import annotations

from app.models.schemas import (
    ConfidenceLevel,
    DiffAtom,
    DiffCompareSchema,
    MissingInfoItem,
    RiskItem,
    RiskLevel,
    RiskReviewSchema,
)
from uuid import uuid4

RISK_KEYWORDS = {
    "auth": RiskLevel.HIGH,
    "password": RiskLevel.HIGH,
    "secret": RiskLevel.HIGH,
    "token": RiskLevel.HIGH,
    "delete": RiskLevel.HIGH,
    "migration": RiskLevel.MEDIUM,
    "config": RiskLevel.MEDIUM,
    "api": RiskLevel.MEDIUM,
    "route": RiskLevel.MEDIUM,
    "test": RiskLevel.LOW,
}


def _classify_atom(atom: DiffAtom) -> tuple[RiskLevel, ConfidenceLevel, str]:
    text = f"{atom.file_path} {atom.symbol} {atom.summary} {atom.route_or_api}".lower()
    level = RiskLevel.LOW
    for kw, rl in RISK_KEYWORDS.items():
        if kw in text:
            level = rl
            break
    if atom.change_type == "removed":
        level = RiskLevel.HIGH
    confidence = ConfidenceLevel.HIGH if atom.symbol else ConfidenceLevel.MEDIUM
    if not atom.symbol and atom.change_type == "modified":
        confidence = ConfidenceLevel.LOW
    title = f"关注 {atom.file_path}"
    if atom.symbol:
        title = f"符号变更: {atom.symbol[:60]}"
    desc = atom.summary or f"文件 {atom.file_path} 发生 {atom.change_type} 变更，建议人工确认上下游影响。"
    return level, confidence, f"{title} — {desc}"


def run_agent4(
    diff: DiffCompareSchema,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
) -> RiskReviewSchema:
    atoms = diff.all_atoms
    if focus_atom_ids:
        focused = [a for a in atoms if a.id in focus_atom_ids]
        atoms = focused if focused else atoms[:10]
    else:
        atoms = atoms[:25]
    risks: list[RiskItem] = []
    missing: list[MissingInfoItem] = []
    degradation: list[str] = []
    for atom in atoms:
        level, confidence, desc = _classify_atom(atom)
        risks.append(
            RiskItem(
                id=str(uuid4())[:8],
                title=desc.split(" — ")[0][:80],
                description=desc,
                risk_level=level,
                confidence=confidence,
                related_atoms=[atom.id],
                file_paths=[atom.file_path],
            )
        )
    if extra_context_paths:
        missing.append(
            MissingInfoItem(
                module="用户补充上下文",
                reason=f"已纳入 {len(extra_context_paths)} 个补充路径",
                suggestion="重跑分析时已提高相关差异点权重",
            )
        )
    if len(diff.all_atoms) > 25 and not focus_atom_ids:
        missing.append(
            MissingInfoItem(
                module="差异对比",
                reason="差异点数量较多，仅审阅前 25 个",
                suggestion="可勾选 1~3 个重点差异点重跑",
            )
        )
        degradation.append("Agent4：差异点截断至 25 个以控制审阅深度（最多扩展 2 层上下文）")
    risks.sort(key=lambda r: (r.risk_level != RiskLevel.HIGH, r.risk_level != RiskLevel.MEDIUM))
    return RiskReviewSchema(risks=risks, missing_info=missing, degradation_notes=degradation)
