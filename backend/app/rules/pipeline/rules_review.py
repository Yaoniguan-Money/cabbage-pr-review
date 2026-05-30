"""规则模式：YAML 规则求值 → RiskReviewSchema（替代 Agent4）。"""

from __future__ import annotations

from app.local.review_depth import get_review_depth_profile
from app.models.schemas import DiffCompareSchema, ReviewStats, RiskReviewSchema
from app.rules.pipeline.rules_aggregate import aggregate_risks_from_hits
from app.rules.rule_evaluator import RuleContext, build_rule_context, evaluate_rule_on_atom
from app.rules.rule_loader import load_rule_pack
from app.rules.rule_schema import RuleHitRecord


def run_rules_review(
    diff: DiffCompareSchema,
    pr_context: dict,
    *,
    review_depth_mode: str = "balanced",
) -> tuple[RiskReviewSchema, list[RuleHitRecord], ReviewStats, list[str]]:
    notes: list[str] = []
    rules, pack_config = load_rule_pack()
    if not rules:
        notes.append("未加载到任何规则，请检查 RULES_PACK_PATH 或默认规则包目录")

    profile = get_review_depth_profile(review_depth_mode)
    max_atoms = min(
        pack_config.scope.max_atoms_per_run,
        profile.atoms_per_batch * profile.max_batches_per_depth * profile.max_depth,
    )
    atoms = diff.all_atoms[:max_atoms]

    ctx = build_rule_context(pr_context)
    hits: list[RuleHitRecord] = []
    seen: set[tuple[str, str, str]] = set()
    related_atoms_by_key: dict[tuple[str, str], list[str]] = {}
    rules_by_id = {rule.id: rule for rule in rules}
    reporting = pack_config.reporting

    for atom in atoms:
        for rule in rules:
            hit = evaluate_rule_on_atom(rule, atom, ctx, reporting=reporting)
            if hit is None:
                continue
            key = (hit.rule_id, hit.file_path, hit.evidence[:80])
            if key in seen:
                continue
            seen.add(key)
            hits.append(hit)
            file_key = (hit.rule_id, hit.file_path)
            related_atoms_by_key.setdefault(file_key, []).append(atom.id)

    risks = aggregate_risks_from_hits(
        hits,
        rules_by_id=rules_by_id,
        reporting=reporting,
        related_atoms_by_key=related_atoms_by_key,
    )

    stats = ReviewStats(
        review_depth_mode=profile.mode,
        review_depth_label="",
        total_atoms=len(diff.all_atoms),
        reviewed_atoms=len(atoms),
        batches_run=1,
        pro_calls=0,
        flash_calls=0,
    )
    review = RiskReviewSchema(risks=risks, degradation_notes=notes)
    return review, hits, stats, notes
