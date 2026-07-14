from __future__ import annotations

import json
from uuid import uuid4

from app.agents.llm_helpers import call_flash_json, call_pro_json
from app.local.context_builder import load_extra_context_files
from app.local.review_depth import ReviewDepthProfile, get_review_depth_option, get_review_depth_profile
from app.models.schemas import (
    AtomContextPlan,
    AtomContextPlanBatch,
    AtomPriorityBatch,
    DiffAtom,
    DiffCompareSchema,
    MissingInfoItem,
    ProjectIndexSchema,
    ReviewStats,
    RiskItem,
    RiskReviewSchema,
)


def _select_focus_atoms(diff: DiffCompareSchema, focus_atom_ids: list[str] | None) -> list[DiffAtom]:
    atoms = diff.all_atoms
    if focus_atom_ids:
        picked = [a for a in atoms if a.id in focus_atom_ids]
        return picked[:10] if picked else atoms[:10]
    return list(atoms)


def _order_atoms_with_flash(
    atoms: list[DiffAtom],
    profile: ReviewDepthProfile,
    stats: ReviewStats,
    notes: list[str],
) -> list[DiffAtom]:
    if not profile.atom_priority_flash_call or len(atoms) <= 1:
        return atoms
    payload = {
        "atoms": [a.model_dump() for a in atoms],
        "instruction": "按审阅优先级输出 ordered_atom_ids（仅排序，不下风险结论）。",
        "json_contract": {"ordered_atom_ids": ["a1", "a2"], "uncovered_reason": ""},
    }
    try:
        batch, n = call_flash_json(
            "你是差异点优先级排序 Agent（Flash）。仅输出 AtomPriorityBatch JSON。",
            json.dumps(payload, ensure_ascii=False),
            AtomPriorityBatch,
        )
        notes.extend(n)
        stats.flash_calls += 1
        id_map = {a.id: a for a in atoms}
        ordered: list[DiffAtom] = []
        seen: set[str] = set()
        for aid in batch.ordered_atom_ids:
            if aid in id_map and aid not in seen:
                ordered.append(id_map[aid])
                seen.add(aid)
        for a in atoms:
            if a.id not in seen:
                ordered.append(a)
        if batch.uncovered_reason.strip():
            notes.append(f"优先级排序说明: {batch.uncovered_reason.strip()}")
        return ordered
    except Exception as e:
        notes.append(f"Flash 优先级排序失败，保持原顺序: {e}")
        return atoms


def _fetch_plan_context(
    plans: list[AtomContextPlan],
    pr_context: dict,
    git_ws: object | None,
    extra_files: dict[str, str],
) -> dict[str, str]:
    collected: dict[str, str] = dict(extra_files)
    paths: set[str] = set()
    for p in plans:
        paths.update(p.layer1_paths)
        paths.update(p.layer2_paths)
    if git_ws and hasattr(git_ws, "read_files_at_ref"):
        head_sha = pr_context.get("head_sha", "")
        collected.update(git_ws.read_files_at_ref(list(paths), head_sha))  # type: ignore[attr-defined]
    return collected


def _dedupe_risks(risks: list[RiskItem]) -> list[RiskItem]:
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, tuple[str, ...]]] = set()
    out: list[RiskItem] = []
    for r in risks:
        if r.id in seen_ids:
            continue
        key = (r.title.strip(), tuple(sorted(r.file_paths)))
        if key in seen_keys and r.title.strip():
            continue
        seen_ids.add(r.id)
        seen_keys.add(key)
        out.append(r)
    return out


def _needs_gap_fill(review: RiskReviewSchema, batch_atoms: list[DiffAtom], profile: ReviewDepthProfile) -> bool:
    if profile.gap_fill_pro_calls_per_batch <= 0 or not batch_atoms:
        return False
    if len(review.risks) < len(batch_atoms):
        return True
    return any(not (r.evidence or "").strip() for r in review.risks)


def _run_batch_review(
    batch_atoms: list[DiffAtom],
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    pr_context: dict,
    extra_files: dict[str, str],
    git_ws: object | None,
    depth: int,
    profile: ReviewDepthProfile,
    stats: ReviewStats,
    notes: list[str],
) -> tuple[RiskReviewSchema, list[AtomContextPlan]]:
    plan_payload = {
        "atoms": [a.model_dump() for a in batch_atoms],
        "base_summary": base.raw_summary,
        "head_summary": head.raw_summary,
        "depth": depth,
        "instruction": (
            "为每个 atom 输出 AtomContextPlan：判断 diff_type，指定 layer1_paths/layer2_paths，"
            "need_deeper 与 new_concerns（必须是字符串数组）。"
        ),
        "json_contract": {
            "plans": [
                {
                    "atom_id": "a1",
                    "diff_type": "route|function|dependency|file",
                    "layer1_paths": ["path/a.py"],
                    "layer2_paths": ["path/b.py"],
                    "need_deeper": False,
                    "new_concerns": ["concern text"],
                }
            ]
        },
    }
    plans_batch, n1 = call_pro_json(
        "你是递进式审阅 Agent 第1步：仅输出 AtomContextPlanBatch，严格遵守 JSON schema，禁止输出解释文本。",
        json.dumps(plan_payload, ensure_ascii=False),
        AtomContextPlanBatch,
    )
    notes.extend(n1)
    stats.pro_calls += 1

    file_ctx = _fetch_plan_context(plans_batch.plans, pr_context, git_ws, extra_files)
    review_payload = {
        "atoms": [a.model_dump() for a in batch_atoms],
        "plans": [p.model_dump() for p in plans_batch.plans],
        "file_context": file_ctx,
        "depth": depth,
        "json_contract": {
            "risks": [
                {
                    "id": "r1",
                    "title": "风险标题",
                    "description": "风险描述",
                    "risk_level": "high|medium|low",
                    "confidence": "high|medium|low",
                    "evidence": "须引用 file_path 与 patch 片段",
                    "suggestion": "建议",
                    "related_atoms": ["a1"],
                    "file_paths": ["path/a.py"],
                    "line_start": 12,
                    "line_end": 12,
                    "category": "security|logic|exception|compatibility|performance|other",
                }
            ],
            "missing_info": [],
            "degradation_notes": [],
        },
    }
    review_part, n2 = call_pro_json(
        "你是递进式审阅 Agent 第2步：仅输出 RiskReviewSchema JSON（含 evidence、suggestion），不要输出额外字段。",
        json.dumps(review_payload, ensure_ascii=False),
        RiskReviewSchema,
    )
    notes.extend(n2)
    stats.pro_calls += 1

    if not review_part.risks and batch_atoms:
        retry_payload = {
            **review_payload,
            "instruction": "仅修正为严格 RiskReviewSchema 结构，不改变语义结论。",
        }
        review_part2, n2_retry = call_pro_json(
            "你是结构纠偏器：只输出严格 RiskReviewSchema JSON，不做额外解释。",
            json.dumps(retry_payload, ensure_ascii=False),
            RiskReviewSchema,
        )
        notes.extend(n2_retry)
        stats.pro_calls += 1
        if review_part2.risks:
            review_part = review_part2

    if _needs_gap_fill(review_part, batch_atoms, profile):
        gap_payload = {
            **review_payload,
            "existing_risks": [r.model_dump() for r in review_part.risks],
            "instruction": (
                "在不改变已有风险结论前提下，补全遗漏风险与非空 evidence；仅输出 RiskReviewSchema。"
            ),
        }
        gap_part, n_gap = call_pro_json(
            "你是风险补全 Agent：补遗漏项与 evidence，仅输出 RiskReviewSchema JSON。",
            json.dumps(gap_payload, ensure_ascii=False),
            RiskReviewSchema,
        )
        notes.extend(n_gap)
        stats.pro_calls += 1
        if gap_part.risks:
            review_part.risks = _dedupe_risks(review_part.risks + gap_part.risks)
        if gap_part.missing_info:
            review_part.missing_info.extend(gap_part.missing_info)

    review_part.risks = _dedupe_risks(review_part.risks)
    return review_part, plans_batch.plans


def run_agent4(
    diff: DiffCompareSchema,
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    pr_context: dict,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
    git_ws: object | None = None,
    review_depth_mode: str = "balanced",
) -> tuple[RiskReviewSchema, list[str], ReviewStats]:
    notes: list[str] = []
    profile = get_review_depth_profile(review_depth_mode)
    depth_opt = get_review_depth_option(review_depth_mode)
    stats = ReviewStats(
        review_depth_mode=profile.mode,
        review_depth_label=depth_opt.label,
        total_atoms=len(diff.all_atoms),
    )

    extra_files = load_extra_context_files(pr_context, extra_context_paths or [], git_ws)
    if focus_atom_ids:
        ordered_atoms = _select_focus_atoms(diff, focus_atom_ids)
    else:
        ordered_atoms = _order_atoms_with_flash(diff.all_atoms, profile, stats, notes)

    all_risks: list[RiskItem] = []
    missing: list[MissingInfoItem] = []
    queue = list(ordered_atoms)
    reviewed_ids: set[str] = set()
    depth = 0
    pending_plans: list[AtomContextPlan] = []

    while (queue or pending_plans) and depth < profile.max_depth:
        if not queue and pending_plans:
            for plan in pending_plans:
                if plan.need_deeper and plan.new_concerns:
                    for concern in plan.new_concerns[:3]:
                        queue.append(
                            DiffAtom(
                                id=str(uuid4())[:8],
                                file_path=plan.layer1_paths[0] if plan.layer1_paths else "unknown",
                                change_type="modified",
                                summary=concern,
                            )
                        )
            pending_plans = []
            if not queue:
                break

        batches_run = 0
        while queue and batches_run < profile.max_batches_per_depth:
            batch_atoms = queue[: profile.atoms_per_batch]
            queue = queue[profile.atoms_per_batch :]
            if not batch_atoms:
                break

            review_part, batch_plans = _run_batch_review(
                batch_atoms,
                base,
                head,
                pr_context,
                extra_files,
                git_ws,
                depth,
                profile,
                stats,
                notes,
            )
            all_risks.extend(review_part.risks)
            missing.extend(review_part.missing_info)
            pending_plans.extend(batch_plans)
            for a in batch_atoms:
                reviewed_ids.add(a.id)
            stats.batches_run += 1
            batches_run += 1

        depth += 1

    all_risks = _dedupe_risks(all_risks)
    stats.reviewed_atoms = len(reviewed_ids)

    max_reviewable = profile.atoms_per_batch * profile.max_batches_per_depth
    if len(diff.all_atoms) > max_reviewable and not focus_atom_ids:
        missing.append(
            MissingInfoItem(
                module="差异对比",
                reason=(
                    f"递进审阅已扫描 {stats.reviewed_atoms}/{stats.total_atoms} 个差异点"
                    f"（模式={depth_opt.label}，每层最多 {max_reviewable} 个）"
                ),
                suggestion="可勾选 1~3 个重点差异点重跑，或选用深度审阅模式",
            )
        )
    if extra_context_paths:
        missing.append(
            MissingInfoItem(
                module="用户补充上下文",
                reason=f"已加载 {len(extra_files)} 个补充文件",
                suggestion="重跑时已纳入补充路径",
            )
        )

    return (
        RiskReviewSchema(risks=all_risks, missing_info=missing, degradation_notes=[]),
        notes,
        stats,
    )
