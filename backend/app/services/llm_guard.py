from fastapi import HTTPException

from app.agents.llm_helpers import LLMRequiredError
from app.config import settings


def ensure_llm_for_api() -> None:
    if settings.use_mock_llm:
        return
    if not settings.llm_enabled:
        raise HTTPException(
            status_code=503,
            detail="未配置 DeepSeek API：请设置 DEEPSEEK_API_KEY 且 USE_MOCK_LLM=false",
        )
    try:
        from app.agents.llm_helpers import _ensure_llm

        _ensure_llm()
    except LLMRequiredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
