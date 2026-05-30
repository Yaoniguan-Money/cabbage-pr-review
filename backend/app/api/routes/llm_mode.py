from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.local.llm_mode import list_llm_mode_options
from app.llm.router import cloud_available, list_local_models, local_available

router = APIRouter(prefix="/api", tags=["llm-mode"])


@router.get("/llm-mode-options")
async def llm_mode_options():
    return list_llm_mode_options(
        default_mode=settings.llm_mode,
        default_compress_enabled=settings.local_compress_enabled,
        cloud_available=cloud_available(),
        local_available=local_available(),
        local_models=list_local_models(),
        default_local_model=settings.local_llm_default_model,
    )
