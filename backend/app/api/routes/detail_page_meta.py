from __future__ import annotations

from fastapi import APIRouter

from app.local.detail_page_meta import list_detail_page_meta

router = APIRouter(prefix="/api", tags=["detail-page-meta"])


@router.get("/detail-page-meta")
async def detail_page_meta():
    return list_detail_page_meta()
