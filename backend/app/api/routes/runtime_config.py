from __future__ import annotations

from fastapi import APIRouter

from app.llm.credentials_resolve import resolve_github_token, server_cloud_configured, server_github_configured
from app.llm.router import cloud_available, local_available
from app.local.provider_presets import list_provider_presets
from app.local.runtime_config_meta import list_runtime_config_meta
from app.models.schemas import RuntimeConfigPreviewRequest, RuntimeConfigPreviewResponse

router = APIRouter(prefix="/api", tags=["runtime-config"])


@router.get("/runtime-config-meta")
async def runtime_config_meta():
    return list_runtime_config_meta()


@router.get("/provider-presets")
async def provider_presets():
    return list_provider_presets()


@router.post("/runtime-config/preview", response_model=RuntimeConfigPreviewResponse)
async def runtime_config_preview(body: RuntimeConfigPreviewRequest) -> RuntimeConfigPreviewResponse:
    creds = body.runtime_credentials
    has_runtime_key = bool(creds and creds.cloud_api_key and creds.cloud_api_key.strip())
    gh = resolve_github_token(creds)
    return RuntimeConfigPreviewResponse(
        cloud_available=cloud_available(
            runtime_credentials=creds,
            has_runtime_cloud_key=has_runtime_key,
        ),
        github_token_configured=bool(gh.strip()),
        local_available=local_available(),
        server_cloud_configured=server_cloud_configured(),
        server_github_configured=server_github_configured(),
    )
