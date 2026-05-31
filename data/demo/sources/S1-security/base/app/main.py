"""FastAPI 应用入口。"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.logging.config import configure_logging
from app.routes import auth, health

logger = logging.getLogger(__name__)

configure_logging()
app = FastAPI(title="demo-security-app", version="0.9.0")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


def root_handler() -> dict[str, Any]:
    return {"ok": True}


def service_metadata() -> dict[str, str]:
    return {
        "service": "demo-security-app",
        "version": "0.9.0",
    }


def build_startup_report() -> dict[str, Any]:
    return {
        "routers": ["health", "auth"],
        "logging": "configured",
    }
