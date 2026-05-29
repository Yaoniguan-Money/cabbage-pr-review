from __future__ import annotations

import json
from uuid import uuid4

from app.agents.llm_helpers import call_pro_json
from app.local.context_builder import load_extra_context_files
from app.models.schemas import (
    AtomContextPlan,
    AtomContextPlanBatch,
    DiffAtom,
    DiffCompareSchema,
    MissingInfoItem,
    ProjectIndexSchema,
    RiskItem,
    RiskReviewSchema,
)

MAX_ATOMS = 25
MAX_DEPTH = 2


def _select_atoms(diff: DiffCompareSchema, focus_atom_ids: list[str] | None) -> list[DiffAtom]:
    atoms = diff.all_atoms
    if focus_atom_ids:
        picked = [a for a in atoms if a.id in focus_atom_ids]
        return picked[:10] if picked else atoms[:10]
    return atoms[:MAX_ATOMS]


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


def run_agent4(
    diff: DiffCompareSchema,
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    pr_context: dict,
    focus_atom_ids: list[str] | None = None,
    extra_context_paths: list[str] | None = None,
    git_ws: object | None = None,
) -> tuple[RiskReviewSchema, list[str]]:
    notes: list[str] = []
    atoms = _select_atoms(diff, focus_atom_ids)
    extra_files = load_extra_context_files(pr_context, extra_context_paths or [], git_ws)

    all_risks: list[RiskItem] = []
    missing: list[MissingInfoItem] = []
    queue = list(atoms)
    depth = 0

    while queue and depth < MAX_DEPTH:
        batch_atoms = queue[:MAX_ATOMS]
        queue = queue[MAX_ATOMS:]

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
                        "evidence": "证据",
                        "suggestion": "建议",
                        "related_atoms": ["a1"],
                        "file_paths": ["path/a.py"],
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
            if review_part2.risks:
                review_part = review_part2
        all_risks.extend(review_part.risks)
        missing.extend(review_part.missing_info)

        if depth + 1 < MAX_DEPTH:
            for plan in plans_batch.plans:
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
        depth += 1

    if len(diff.all_atoms) > MAX_ATOMS and not focus_atom_ids:
        missing.append(
            MissingInfoItem(
                module="差异对比",
                reason=f"差异原子共 {len(diff.all_atoms)} 个，递进审阅每层最多 {MAX_ATOMS} 个",
                suggestion="可勾选 1~3 个重点差异点重跑",
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

    return RiskReviewSchema(risks=all_risks, missing_info=missing, degradation_notes=[]), notes
