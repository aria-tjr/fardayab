from __future__ import annotations

import time
from typing import Any


_CACHE: dict[str, tuple[float, Any]] = {}


def get(key: str) -> Any | None:
    v = _CACHE.get(key)
    if not v:
        return None
    exp, val = v
    if exp < time.time():
        _CACHE.pop(key, None)
        return None
    return val


def set(key: str, val: Any, ttl: int) -> None:
    _CACHE[key] = (time.time() + ttl, val)

