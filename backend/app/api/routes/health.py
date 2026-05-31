from fastapi import APIRouter

from app.config import settings
from app.local.llm_mode import VALID_LLM_MODES
from app.llm.router import cloud_available, list_local_models, local_available
from app.rules.rule_loader import load_rule_pack_with_lint

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    rules, _, lint_issues = load_rule_pack_with_lint()
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "use_mock_llm": settings.use_mock_llm,
        "model_profile": "v22_provider_via_env",
        "llm_mode": settings.llm_mode,
        "llm_mode_count": len(VALID_LLM_MODES),
        "cloud_available": cloud_available(),
        "local_available": local_available(),
        "rules_pack_loaded": len(rules) > 0,
        "rules_count": len(rules),
        "rules_invalid_count": len(lint_issues),
        "cloud_flash_model": settings.cloud_flash_model_resolved,
        "cloud_pro_model": settings.cloud_pro_model_resolved,
        "local_llm_base_url": settings.local_llm_base_url,
        "local_compress_enabled_default": settings.local_compress_enabled,
        "default_review_depth_mode": settings.review_depth_mode,
        # 兼容旧客户端
        "deepseek_flash_model": settings.cloud_flash_model_resolved,
        "deepseek_pro_model": settings.cloud_pro_model_resolved,
    }
