from __future__ import annotations

from fastapi import APIRouter

from app.local.rule_meta import list_rules_meta

router = APIRouter(prefix="/api", tags=["rules-meta"])


@router.get("/rules-meta")
async def rules_meta():
    return list_rules_meta()
