from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "use_mock_llm": settings.use_mock_llm,
        "model_profile": "v4_flash_pro_via_env",
        "deepseek_flash_model": settings.deepseek_flash_model,
        "deepseek_pro_model": settings.deepseek_pro_model,
        "default_review_depth_mode": settings.review_depth_mode,
    }
