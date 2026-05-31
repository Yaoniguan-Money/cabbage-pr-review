"""应用程序全局配置模块。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
APP_NAME = "demo-security-app"
APP_VERSION = "0.9.0"


@dataclass(frozen=True)
class DatabaseConfig:
    driver: str = "sqlite"
    path: str = str(BASE_DIR / "var" / "app.db")
    pool_size: int = 5
    echo: bool = False


@dataclass(frozen=True)
class SecurityConfig:
    token_ttl_seconds: int = 3600
    password_min_length: int = 8
    bcrypt_rounds: int = 12
    allow_plaintext_secrets: bool = False


def get_database_url(cfg: DatabaseConfig | None = None) -> str:
    db = cfg or DatabaseConfig()
    if db.driver == "sqlite":
        return f"sqlite:///{db.path}"
    return f"{db.driver}://localhost/{db.path}"


def load_redis_settings() -> dict[str, Any]:
    return {
        "host": os.getenv("REDIS_HOST", "127.0.0.1"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "socket_timeout": 2.0,
    }


DATABASE = DatabaseConfig()
SECURITY = SecurityConfig()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
REQUEST_TIMEOUT_SECONDS = 30
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ENABLE_METRICS = True
METRICS_PREFIX = "demo_security"
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
SHUTDOWN_GRACE_SECONDS = 15


def as_dict() -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "debug": DEBUG,
        "log_level": LOG_LEVEL,
        "database": get_database_url(DATABASE),
    }
