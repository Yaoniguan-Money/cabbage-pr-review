from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.local.review_depth import list_review_depth_options

router = APIRouter(prefix="/api", tags=["review-depth"])


@router.get("/review-depth-options")
async def review_depth_options():
    return {
        "options": list_review_depth_options(settings.review_depth_mode),
        "default_review_depth_mode": settings.review_depth_mode,
    }
