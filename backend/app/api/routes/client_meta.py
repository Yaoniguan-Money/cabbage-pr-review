from __future__ import annotations

from fastapi import APIRouter

from app.local.client_meta import list_client_meta

router = APIRouter(prefix="/api", tags=["client-meta"])


@router.get("/client-meta")
async def client_meta():
    return list_client_meta()
