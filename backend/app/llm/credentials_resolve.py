"""运行时凭据解析：public 部署忽略服务器 Key，仅认任务级凭据。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from app.models.schemas import RuntimeCredentials

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedCloudConfig:
    api_base: str
    api_key: str
    flash_model: str
    pro_model: str


def is_public_deploy() -> bool:
    return settings.deploy_mode.strip().lower() == "public"


def server_cloud_configured() -> bool:
    if is_public_deploy():
        if settings.cloud_api_key_resolved:
            logger.warning("DEPLOY_MODE=public：已忽略服务器中的云端 API Key")
        return False
    if not settings.effective_use_server_cloud_credentials:
        return False
    return bool(settings.cloud_api_key_resolved)


def server_github_configured() -> bool:
    if is_public_deploy():
        if settings.github_token.strip():
            logger.warning("DEPLOY_MODE=public：已忽略服务器中的 GITHUB_TOKEN")
        return False
    if not settings.effective_use_server_github_token:
        return False
    return bool(settings.github_token.strip())


def _strip(value: str | None) -> str:
    return (value or "").strip()


def credentials_has_cloud(creds: RuntimeCredentials | None) -> bool:
    if creds is None:
        return False
    return bool(_strip(creds.cloud_api_key))


def resolve_cloud_config(
    creds: RuntimeCredentials | None,
    *,
    cloud_flash_model: str | None = None,
    cloud_pro_model: str | None = None,
) -> ResolvedCloudConfig | None:
    key = _strip(creds.cloud_api_key if creds else None)
    if not key:
        if is_public_deploy() or not settings.effective_use_server_cloud_credentials:
            return None
        key = settings.cloud_api_key_resolved
        if not key:
            return None
    base = _strip(creds.cloud_api_base if creds else None) or settings.cloud_api_base_resolved
    flash = (
        _strip(creds.cloud_flash_model if creds else None)
        or _strip(cloud_flash_model)
        or settings.cloud_flash_model_resolved
    )
    pro = (
        _strip(creds.cloud_pro_model if creds else None)
        or _strip(cloud_pro_model)
        or settings.cloud_pro_model_resolved
    )
    return ResolvedCloudConfig(api_base=base, api_key=key, flash_model=flash, pro_model=pro)


def resolve_github_token(creds: RuntimeCredentials | None) -> str:
    token = _strip(creds.github_token if creds else None)
    if token:
        return token
    if is_public_deploy() or not settings.effective_use_server_github_token:
        return ""
    return settings.github_token.strip()


def cloud_available_for_request(
    creds: RuntimeCredentials | None,
    *,
    has_runtime_cloud_key: bool = False,
) -> bool:
    if settings.use_mock_llm:
        return True
    if credentials_has_cloud(creds) or has_runtime_cloud_key:
        return True
    return server_cloud_configured()


def task_cloud_available(ctx) -> bool:
    from app.llm.task_context import TaskLLMContext

    if not isinstance(ctx, TaskLLMContext):
        return False
    return bool(_strip(ctx.cloud_api_key))
