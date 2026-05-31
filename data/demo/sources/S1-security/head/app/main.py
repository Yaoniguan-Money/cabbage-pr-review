"""FastAPI 应用入口。"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.logging.config import configure_logging
from app.routes import auth, health
from config import settings

logger = logging.getLogger(__name__)

configure_logging()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


def root_handler() -> dict[str, Any]:
    meta = service_metadata()
    return {
        "ok": True,
        "service": meta["service"],
        "version": meta["version"],
        "maintenance_mode": settings.MAINTENANCE_MODE,
    }


def service_metadata() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "production" if not settings.DEBUG else "development",
    }


def build_startup_report() -> dict[str, Any]:
    return {
        "routers": ["health", "auth"],
        "logging": "configured",
        "metrics_enabled": settings.ENABLE_METRICS,
        "audit_enabled": settings.AUDIT_LOG_ENABLED,
        "rate_limit": settings.RATE_LIMIT_PER_MINUTE,
    }


def runtime_capabilities() -> dict[str, bool]:
    return {
        "streaming_logs": settings.FEATURE_STREAMING_LOGS,
        "debug_traceback": settings.FEATURE_DEBUG_TRACEBACK,
        "pii_masking": settings.PII_MASKING_ENABLED,
        "encryption_at_rest": settings.ENCRYPTION_AT_REST,
    }


def compose_health_summary(checks: dict[str, bool]) -> dict[str, Any]:
    overall = all(checks.values()) if checks else False
    return {
        "healthy": overall,
        "checks": checks,
        "service": settings.APP_NAME,
    }


def list_public_endpoints() -> list[str]:
    return [
        "/health/live",
        "/health/ready",
        "/auth/login",
        "/auth/logout",
        "/auth/profile",
    ]


def describe_security_posture() -> dict[str, Any]:
    return {
        "session_cookie_secure": settings.SESSION_COOKIE_SECURE,
        "session_cookie_httponly": settings.SESSION_COOKIE_HTTPONLY,
        "login_max_attempts": settings.LOGIN_MAX_ATTEMPTS,
        "login_lockout_minutes": settings.LOGIN_LOCKOUT_MINUTES,
        "trusted_proxy_count": settings.TRUSTED_PROXY_COUNT,
    }


def export_runtime_config() -> dict[str, Any]:
    return {
        "startup": build_startup_report(),
        "capabilities": runtime_capabilities(),
        "security": describe_security_posture(),
        "settings": settings.as_dict(),
    }
