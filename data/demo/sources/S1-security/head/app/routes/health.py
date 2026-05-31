"""健康检查路由处理函数。"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
_started_at = time.time()


def live_handler() -> dict[str, Any]:
    return {
        "status": "alive",
        "uptime_seconds": int(time.time() - _started_at),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


def ready_handler() -> dict[str, Any]:
    checks = {
        "database": check_database(),
        "token_store": check_token_store(),
        "redis": check_redis(),
        "audit_log": check_audit_log(),
    }
    healthy = all(checks.values())
    return {
        "status": "ready" if healthy else "degraded",
        "checks": checks,
        "maintenance_mode": settings.MAINTENANCE_MODE,
    }


def check_database() -> bool:
    url = settings.get_database_url(settings.DATABASE)
    logger.debug("数据库探活 url=%s", url)
    return bool(url)


def check_token_store() -> bool:
    return settings.SECURITY.token_ttl_seconds > 0


def check_redis() -> bool:
    redis_cfg = settings.load_redis_settings()
    return bool(redis_cfg.get("host"))


def check_audit_log() -> bool:
    if not settings.AUDIT_LOG_ENABLED:
        return True
    return bool(settings.AUDIT_LOG_PATH)


def detailed_handler() -> dict[str, Any]:
    return {
        "service": settings.APP_NAME,
        "metrics_enabled": settings.ENABLE_METRICS,
        "worker_concurrency": settings.WORKER_CONCURRENCY,
        "healthcheck_stale_seconds": settings.HEALTHCHECK_STALE_SECONDS,
    }


def dependency_matrix() -> dict[str, bool]:
    return {
        "database": check_database(),
        "token_store": check_token_store(),
        "redis": check_redis(),
        "audit_log": check_audit_log(),
    }


def summarize_readiness() -> dict[str, Any]:
    checks = dependency_matrix()
    return {
        "healthy": all(checks.values()),
        "checks": checks,
        "uptime_seconds": int(time.time() - _started_at),
    }
