from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Mapping, Protocol, runtime_checkable

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError


@runtime_checkable
class RedisLike(Protocol):
    def hgetall(self, name: str) -> dict[str, str]: ...

    def hset(
            self,
            name: str,
            key: str | None = None,
            value: str | None = None,
            mapping: Mapping[str, Any] | None = None,
    ) -> int: ...

    def hdel(self, name: str, *keys: str) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...


class _MemoryRedis:
    def __init__(self) -> None:
        self._h: dict[str, dict[str, str]] = {}

    def hgetall(self, name: str) -> dict[str, str]:
        return dict(self._h.get(name, {}))

    def hset(
            self,
            name: str,
            key: str | None = None,
            value: str | None = None,
            mapping: Mapping[str, Any] | None = None,
    ) -> int:
        self._h.setdefault(name, {})

        written = 0
        if mapping:
            for k, v in mapping.items():
                self._h[name][str(k)] = str(v)
                written += 1

        if key is not None and value is not None:
            self._h[name][str(key)] = str(value)
            written += 1

        return written

    def hdel(self, name: str, *keys: str) -> int:
        if name not in self._h:
            return 0
        cnt = 0
        for k in keys:
            if k in self._h[name]:
                del self._h[name][k]
                cnt += 1
        return cnt

    def expire(self, name: str, time: int) -> bool:
        # TTL not implemented for in-memory backend (dev only)
        _ = name
        _ = time
        return True


_memory_singleton: RedisLike = _MemoryRedis()


@lru_cache
def get_redis() -> RedisLike:
    url = os.getenv("REDIS_URL")
    env = os.getenv("ENV", "dev")
    if not url:
        if env == "prod":
            raise RuntimeError("REDIS_URL is missing in production")
        return _memory_singleton

    r: Redis = Redis.from_url(url, decode_responses=True)
    try:
        r.ping()
        return r
    except RedisConnectionError as e:
        if env == "prod":
            raise RuntimeError(f"Redis connection failed in production: {e}") from e
        return _memory_singleton
