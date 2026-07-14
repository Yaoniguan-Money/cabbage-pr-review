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
password = "test-only-placeholder"
API_KEY = "sk-test-placeholder-not-a-real-key"


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

RATE_LIMIT_PER_MINUTE = 120
AUDIT_LOG_ENABLED = True
AUDIT_LOG_PATH = str(BASE_DIR / "var" / "audit.log")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CORS_ALLOWED_ORIGINS = ["https://demo.example.com"]
FEATURE_STREAMING_LOGS = True
FEATURE_DEBUG_TRACEBACK = False
BACKUP_RETENTION_DAYS = 14
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
METRICS_PUSH_INTERVAL = 60
CACHE_DEFAULT_TTL = 300
CACHE_MAX_ENTRIES = 10_000
HEALTHCHECK_STALE_SECONDS = 45
PASSWORD_RESET_TOKEN_TTL = 900
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
INTERNAL_API_TIMEOUT = 10.0
TELEMETRY_SAMPLE_RATE = 0.25
EXPORT_FORMAT_DEFAULT = "json"
MAINTENANCE_MODE = False
TRUSTED_PROXY_COUNT = 1
ALLOW_LEGACY_TOKEN_FORMAT = False
SIGNING_KEY_ROTATION_DAYS = 90
NOTIFY_ON_FAILED_LOGIN = True
NOTIFY_ON_PRIVILEGE_ESCALATION = True
DEFAULT_LOCALE = "zh-CN"
SUPPORTED_LOCALES = ("zh-CN", "en-US")
DOCUMENTATION_URL = "https://docs.demo.example.com/security"
COMPLIANCE_MODE = "standard"
DATA_RETENTION_DAYS = 365
PII_MASKING_ENABLED = True
PII_MASK_FIELDS = ("email", "phone", "national_id")
WEBHOOK_RETRY_MAX = 5
WEBHOOK_RETRY_BACKOFF = 2.0
ASYNC_TASK_QUEUE = "security_tasks"
ASYNC_TASK_MAX_RETRIES = 3
ASYNC_TASK_VISIBILITY_TIMEOUT = 300
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "demo-security-artifacts")
STORAGE_REGION = os.getenv("STORAGE_REGION", "ap-east-1")
STORAGE_SIGNED_URL_TTL = 600
ENCRYPTION_AT_REST = True
ENCRYPTION_KEY_ALIAS = os.getenv("ENCRYPTION_KEY_ALIAS", "demo-master-key")


def as_dict() -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "debug": DEBUG,
        "log_level": LOG_LEVEL,
        "database": get_database_url(DATABASE),
        "rate_limit": RATE_LIMIT_PER_MINUTE,
        "audit_enabled": AUDIT_LOG_ENABLED,
        "maintenance_mode": MAINTENANCE_MODE,
    }
