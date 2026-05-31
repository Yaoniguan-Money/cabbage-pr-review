from __future__ import annotations

from fastapi import APIRouter

from app.local.diagram_meta import OVERVIEW_RISK_PREVIEW_COUNT
from app.local.rule_meta import RULES_PACK_VERSION, list_rules_meta
from app.rules.rule_loader import list_rules_catalog, load_rule_pack_with_lint

router = APIRouter(prefix="/api", tags=["rules-meta"])


@router.get("/rules-meta")
async def rules_meta():
    return list_rules_meta(overview_risk_preview_count=OVERVIEW_RISK_PREVIEW_COUNT)


@router.get("/rules-catalog")
async def rules_catalog():
    rules, _, lint_issues = load_rule_pack_with_lint()
    return {
        "rules_count": len(rules),
        "rules_invalid_count": len(lint_issues),
        "rules_pack_version": RULES_PACK_VERSION,
        "rules": list_rules_catalog(rules),
    }
