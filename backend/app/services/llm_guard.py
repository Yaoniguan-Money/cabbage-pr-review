from fastapi import HTTPException

from app.agents.llm_helpers import LLMRequiredError
from app.config import settings
from app.local.llm_mode import HINT_CLOUD_UNAVAILABLE, normalize_llm_mode, validate_task_llm_config
from app.llm.router import cloud_available, local_available


def ensure_llm_for_api(
    *,
    llm_mode: str | None = None,
    local_compress_enabled: bool | None = None,
    local_model: str | None = None,
) -> None:
    if settings.use_mock_llm:
        return

    mode = normalize_llm_mode(llm_mode, settings.llm_mode)
    compress = settings.local_compress_enabled if local_compress_enabled is None else local_compress_enabled
    if mode != "hybrid":
        compress = False

    err = validate_task_llm_config(
        llm_mode=mode,
        local_compress_enabled=compress,
        local_model=local_model or settings.local_llm_default_model,
        cloud_available=cloud_available(),
        local_available=local_available(),
    )
    if err:
        raise HTTPException(status_code=503, detail=err)

    if mode == "local_only":
        return

    if not cloud_available():
        raise HTTPException(status_code=503, detail=HINT_CLOUD_UNAVAILABLE)

    try:
        from app.agents.llm_helpers import _ensure_llm

        _ensure_llm()
    except LLMRequiredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
