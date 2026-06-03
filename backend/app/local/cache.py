from __future__ import annotations

import threading
import time
from typing import Any

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK = threading.Lock()
_DEFAULT_TTL = 300


def cache_get(key: str) -> Any | None:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        expires, value = item
        if time.time() > expires:
            _CACHE.pop(key, None)  # pop 安全，不会因并发 del 抛 KeyError
            return None
        return value


def cache_set(key: str, value: Any, ttl: int = _DEFAULT_TTL) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time() + ttl, value)
