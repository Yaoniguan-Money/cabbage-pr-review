from __future__ import annotations

from fastapi import APIRouter

from app.local.diagram_meta import list_diagram_meta

router = APIRouter(prefix="/api", tags=["diagram-meta"])


@router.get("/diagram-meta")
async def diagram_meta():
    return list_diagram_meta()
