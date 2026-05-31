"""应用日志配置。"""
from __future__ import annotations

import logging.config
from pathlib import Path
from typing import Any

from config import settings


def build_logging_config(level: str | None = None) -> dict[str, Any]:
    resolved_level = level or settings.LOG_LEVEL
    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": resolved_level,
        },
    }
    if settings.FEATURE_STREAMING_LOGS:
        log_dir = Path(settings.AUDIT_LOG_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": str(log_dir / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "level": resolved_level,
        }
    root_handlers = list(handlers.keys())
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.LOG_FORMAT,
            },
            "audit": {
                "format": "%(asctime)s AUDIT [%(name)s] %(message)s",
            },
        },
        "handlers": handlers,
        "loggers": {
            "app.routes.auth": {
                "handlers": root_handlers,
                "level": resolved_level,
                "propagate": False,
            },
            "app.runtime.executor": {
                "handlers": root_handlers,
                "level": "WARNING" if not settings.DEBUG else resolved_level,
                "propagate": False,
            },
        },
        "root": {
            "handlers": root_handlers,
            "level": resolved_level,
        },
    }


def configure_logging(level: str | None = None) -> None:
    logging.config.dictConfig(build_logging_config(level))


def audit_logger(name: str = "security.audit") -> logging.Logger:
    return logging.getLogger(name)


def describe_logging_state() -> dict[str, Any]:
    config = build_logging_config()
    return {
        "level": config["root"]["level"],
        "handlers": list(config["handlers"].keys()),
        "streaming_logs": settings.FEATURE_STREAMING_LOGS,
    }
