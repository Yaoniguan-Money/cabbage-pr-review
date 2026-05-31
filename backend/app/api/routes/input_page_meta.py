from __future__ import annotations

from fastapi import APIRouter

from app.local.input_page_meta import list_input_page_meta

router = APIRouter(prefix="/api", tags=["input-page-meta"])


@router.get("/input-page-meta")
async def input_page_meta():
    return list_input_page_meta()
