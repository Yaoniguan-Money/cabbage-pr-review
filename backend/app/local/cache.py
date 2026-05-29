from __future__ import annotations

import time
from typing import Any

_CACHE: dict[str, tuple[float, Any]] = {}
_DEFAULT_TTL = 300


def cache_get(key: str) -> Any | None:
    item = _CACHE.get(key)
    if not item:
        return None
    expires, value = item
    if time.time() > expires:
        del _CACHE[key]
        return None
    return value


def cache_set(key: str, value: Any, ttl: int = _DEFAULT_TTL) -> None:
    _CACHE[key] = (time.time() + ttl, value)
