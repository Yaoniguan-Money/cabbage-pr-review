"""健康检查路由处理函数。"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()
_started_at = time.time()


def live_handler() -> dict[str, Any]:
    return {"status": "alive", "uptime_seconds": int(time.time() - _started_at)}


def ready_handler() -> dict[str, Any]:
    checks = {
        "database": check_database(),
        "token_store": check_token_store(),
    }
    healthy = all(checks.values())
    return {"status": "ready" if healthy else "degraded", "checks": checks}


def check_database() -> bool:
    return True


def check_token_store() -> bool:
    return True
