from __future__ import annotations

from fastapi import APIRouter

from app.local.demo_patches_meta import list_demo_patches

router = APIRouter(prefix="/api", tags=["demo-patches"])


@router.get("/demo-patches")
async def demo_patches():
    return list_demo_patches()
