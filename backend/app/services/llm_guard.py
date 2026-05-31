from fastapi import HTTPException

from app.agents.llm_helpers import LLMRequiredError
from app.config import settings
from app.local.llm_mode import (
    is_rules_only_mode,
    normalize_llm_mode,
    resolve_cloud_unavailable_hint,
    validate_task_llm_config,
)
from app.llm.router import cloud_available, local_available
from app.models.schemas import RuntimeCredentials


def ensure_llm_for_api(
    *,
    llm_mode: str | None = None,
    local_compress_enabled: bool | None = None,
    local_model: str | None = None,
    runtime_credentials: RuntimeCredentials | None = None,
) -> None:
    if settings.use_mock_llm:
        return

    if runtime_credentials and not settings.allow_runtime_credentials:
        raise HTTPException(status_code=400, detail="当前部署不允许在请求中携带运行时凭据")

    mode = normalize_llm_mode(llm_mode, settings.llm_mode)
    if is_rules_only_mode(mode):
        return

    compress = settings.local_compress_enabled if local_compress_enabled is None else local_compress_enabled
    if mode != "hybrid":
        compress = False

    cloud_ok = cloud_available(runtime_credentials=runtime_credentials)

    err = validate_task_llm_config(
        llm_mode=mode,
        local_compress_enabled=compress,
        local_model=local_model or settings.local_llm_default_model,
        cloud_available=cloud_ok,
        local_available=local_available(),
    )
    if err:
        raise HTTPException(status_code=503, detail=err)

    if mode == "local_only":
        return

    if not cloud_ok:
        raise HTTPException(status_code=503, detail=resolve_cloud_unavailable_hint())

    try:
        from app.agents.llm_helpers import _ensure_llm

        _ensure_llm()
    except LLMRequiredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
