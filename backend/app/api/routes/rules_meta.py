from __future__ import annotations

from fastapi import APIRouter

from app.local.diagram_meta import OVERVIEW_RISK_PREVIEW_COUNT
from app.local.rule_meta import list_rules_meta

router = APIRouter(prefix="/api", tags=["rules-meta"])


@router.get("/rules-meta")
async def rules_meta():
    return list_rules_meta(overview_risk_preview_count=OVERVIEW_RISK_PREVIEW_COUNT)
