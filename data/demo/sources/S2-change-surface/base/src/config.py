"""应用配置（pydantic-settings）。"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8080, alias="APP_PORT")
    app_bind: str = Field(default="0.0.0.0", alias="APP_BIND")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS")
    otel_service_name: str = Field(default="change-surface-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str = Field(default="", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    deploy_region: str = Field(default="us-east-1", alias="DEPLOY_REGION")
    feature_canary: bool = Field(default=False, alias="FEATURE_CANARY")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def settings_snapshot() -> dict[str, str | int | bool]:
    cfg = get_settings()
    return {
        "app_env": cfg.app_env,
        "app_port": cfg.app_port,
        "log_level": cfg.log_level,
        "metrics_enabled": cfg.metrics_enabled,
        "deploy_region": cfg.deploy_region,
        "feature_canary": cfg.feature_canary,
    }


def validate_timeout_window(seconds: int) -> int:
    return max(5, min(seconds, 60))
