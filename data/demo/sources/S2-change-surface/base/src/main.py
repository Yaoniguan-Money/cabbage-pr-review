"""change-surface-api FastAPI 入口。"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


def _collect_route_manifest(cfg: Settings) -> list[dict[str, str]]:
    return [
        {"path": "/health/live", "method": "GET", "owner": "platform"},
        {"path": "/health/ready", "method": "GET", "owner": "platform"},
        {"path": "/metrics", "method": "GET", "owner": "observability"},
        {"path": "/api/v1/info", "method": "GET", "owner": "api"},
        {"path": "/api/v1/deploy", "method": "GET", "owner": "release"},
        {"path": "/api/v1/features", "method": "GET", "owner": "api"},
        {"path": "/api/v1/routes", "method": "GET", "owner": "api"},
    ]


def _feature_flags(cfg: Settings) -> dict[str, bool]:
    return {
        "canary": cfg.feature_canary,
        "metrics": cfg.metrics_enabled,
    }


def register_extended_routes(app: FastAPI, cfg: Settings) -> None:
    @app.get("/api/v1/features")
    def list_features() -> dict[str, Any]:
        return {"environment": cfg.app_env, "features": _feature_flags(cfg)}

    @app.get("/api/v1/routes")
    def route_manifest() -> dict[str, Any]:
        return {"routes": _collect_route_manifest(cfg)}

    @app.get("/api/v1/config/snapshot")
    def config_snapshot() -> dict[str, Any]:
        from src.config import settings_snapshot
        return settings_snapshot()

    @app.get("/api/v1/ops/ping")
    def ops_ping() -> dict[str, str]:
        return {"status": "ok", "region": cfg.deploy_region}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting change-surface-api env=%s port=%s", settings.app_env, settings.app_port)
    yield
    logger.info("Shutting down change-surface-api")


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    app = FastAPI(
        title="change-surface-api",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
        return response

    @app.get("/health/live")
    def health_live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    def health_ready() -> dict[str, Any]:
        return {
            "status": "ready",
            "env": cfg.app_env,
            "metrics_enabled": cfg.metrics_enabled,
        }

    @app.get("/metrics")
    def metrics() -> Response:
        if not cfg.metrics_enabled:
            return Response(status_code=404)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/v1/info")
    def service_info() -> dict[str, Any]:
        return {
            "service": "change-surface-api",
            "version": "1.0.0",
            "environment": cfg.app_env,
        }

    @app.get("/api/v1/deploy")
    def deploy_metadata() -> dict[str, Any]:
        return {
            "service": "change-surface-api",
            "environment": cfg.app_env,
            "image": "ghcr.io/demo-org/change-surface-api",
            "pipeline": "github-actions",
        }

    register_extended_routes(app, cfg)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.app_bind,
        port=settings.app_port,
        log_level=settings.log_level,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
