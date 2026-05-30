"""按 rule_id 聚合风险条目（配置驱动，禁止按规则 id 分支文案）。"""

from __future__ import annotations

from collections import defaultdict

from app.models.schemas import RiskItem
from app.rules.rule_schema import (
    RuleDefinition,
    RuleHitRecord,
    RulePackReporting,
    default_confidence_for_risk,
    map_severity,
)


def aggregate_risks_from_hits(
    hits: list[RuleHitRecord],
    *,
    rules_by_id: dict[str, RuleDefinition],
    reporting: RulePackReporting,
    related_atoms_by_key: dict[tuple[str, str], list[str]],
) -> list[RiskItem]:
    """将命中记录转为风险列表；可按 rule_id 分组以降低重复标题。"""
    if not hits:
        return []

    if not reporting.group_risks_by_rule_id:
        return _risks_per_hit(hits, rules_by_id=rules_by_id, related_atoms_by_key=related_atoms_by_key)

    groups: dict[str, list[RuleHitRecord]] = defaultdict(list)
    for hit in hits:
        groups[hit.rule_id].append(hit)

    risks: list[RiskItem] = []
    for rule_id, group_hits in groups.items():
        rule = rules_by_id.get(rule_id)
        message = group_hits[0].message
        level = map_severity(group_hits[0].severity)

        unique_files: list[str] = []
        seen_files: set[str] = set()
        for hit in group_hits:
            if hit.file_path not in seen_files:
                seen_files.add(hit.file_path)
                unique_files.append(hit.file_path)

        max_listed = max(1, reporting.max_files_listed_per_risk)
        listed = unique_files[:max_listed]
        description = message
        if len(unique_files) > 1:
            description = f"{message}；涉及 {len(unique_files)} 个文件：{', '.join(listed)}"
            if len(unique_files) > max_listed:
                description += f" 等（另有 {len(unique_files) - max_listed} 个）"

        evidence = (group_hits[0].evidence or "").strip()
        if len(unique_files) > 1 and reporting.grouped_evidence_suffix:
            suffix = reporting.grouped_evidence_suffix.format(count=len(unique_files))
            evidence = f"{evidence}；{suffix}" if evidence else suffix
        evidence = evidence[:500]

        meta_suggestion = ""
        if rule and rule.metadata.get("suggestion"):
            meta_suggestion = str(rule.metadata["suggestion"])

        atom_ids: list[str] = []
        for hit in group_hits:
            key = (hit.rule_id, hit.file_path)
            atom_ids.extend(related_atoms_by_key.get(key, []))

        risks.append(
            RiskItem(
                id=f"risk_{len(risks) + 1}",
                title=message,
                description=description,
                risk_level=level,
                confidence=default_confidence_for_risk(level),
                evidence=evidence,
                suggestion=meta_suggestion or f"规则 `{rule_id}` 命中，请人工复核相关变更",
                related_atoms=list(dict.fromkeys(atom_ids)),
                file_paths=unique_files[:50],
            )
        )
    return risks


def _risks_per_hit(
    hits: list[RuleHitRecord],
    *,
    rules_by_id: dict[str, RuleDefinition],
    related_atoms_by_key: dict[tuple[str, str], list[str]],
) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for hit in hits:
        rule = rules_by_id.get(hit.rule_id)
        level = map_severity(hit.severity)
        meta_suggestion = ""
        if rule and rule.metadata.get("suggestion"):
            meta_suggestion = str(rule.metadata["suggestion"])
        key = (hit.rule_id, hit.file_path)
        risks.append(
            RiskItem(
                id=f"risk_{len(risks) + 1}",
                title=hit.message,
                description=hit.message,
                risk_level=level,
                confidence=default_confidence_for_risk(level),
                evidence=hit.evidence,
                suggestion=meta_suggestion or f"规则 `{hit.rule_id}` 命中，请人工复核相关变更",
                related_atoms=list(related_atoms_by_key.get(key, [])),
                file_paths=[hit.file_path],
            )
        )
    return risks
