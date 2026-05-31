"""应用日志配置。"""
from __future__ import annotations

import logging.config
from typing import Any


def build_logging_config(level: str = "INFO") -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": level,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }


def configure_logging(level: str = "INFO") -> None:
    logging.config.dictConfig(build_logging_config(level))
