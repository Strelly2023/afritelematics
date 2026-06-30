"""Redis-backed token bucket for distributed partner enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable
import os
import time

try:  # pragma: no cover - dependency availability is environment-specific
    import redis  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for test/runtime environments
    redis = None


TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

local data = redis.call("HMGET", key, "tokens", "timestamp")
local tokens = tonumber(data[1])
local timestamp = tonumber(data[2])

if tokens == nil or timestamp == nil then
    tokens = capacity
    timestamp = now
end

local elapsed = math.max(0, now - timestamp)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

if tokens < requested then
    redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
    redis.call("EXPIRE", key, ttl)
    return 0
end

tokens = tokens - requested
redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
redis.call("EXPIRE", key, ttl)
return 1
"""


class _FallbackRedisClient:
    def __init__(self) -> None:
        self._hashes: dict[str, dict[str, float]] = {}
        self._strings: dict[str, str] = {}
        self._lock = Lock()

    def register_script(self, script: str):  # noqa: ARG002
        def runner(*, keys, args):
            key = keys[0]
            capacity, refill_rate, now, requested, ttl = args
            with self._lock:
                bucket = self._hashes.setdefault(key, {})
                tokens = float(bucket.get("tokens", capacity))
                timestamp = float(bucket.get("timestamp", now))
                elapsed = max(0.0, float(now) - timestamp)
                tokens = min(float(capacity), tokens + elapsed * float(refill_rate))
                if tokens < float(requested):
                    bucket["tokens"] = tokens
                    bucket["timestamp"] = float(now)
                    return 0
                bucket["tokens"] = tokens - float(requested)
                bucket["timestamp"] = float(now)
                return 1

        return runner

    def incr(self, key: str) -> int:
        with self._lock:
            value = int(float(self._strings.get(key, "0"))) + 1
            self._strings[key] = str(value)
            return value

    def expire(self, key: str, ttl: int) -> None:  # noqa: ARG002
        return None

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        with self._lock:
            self._strings[key] = str(value)

    def get(self, key: str):
        with self._lock:
            return self._strings.get(key)

    def delete(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._strings.pop(key, None)
                self._hashes.pop(key, None)


_FALLBACK_REDIS_CLIENT = _FallbackRedisClient()


@dataclass
class RedisTokenBucketLimiter:
    client: Any
    key_prefix: str = "governance:rate_limit"
    ttl_seconds: int = 60

    def __post_init__(self) -> None:
        self._script: Callable[..., Any] = self.client.register_script(TOKEN_BUCKET_LUA)

    @classmethod
    def from_url(
        cls,
        redis_url: str | None = None,
        *,
        key_prefix: str = "governance:rate_limit",
        ttl_seconds: int = 60,
    ) -> "RedisTokenBucketLimiter":
        if redis is None:
            client = _FALLBACK_REDIS_CLIENT
        else:
            client = redis.Redis.from_url(redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        return cls(client=client, key_prefix=key_prefix, ttl_seconds=ttl_seconds)

    def allow_request(
        self,
        org_id: str,
        *,
        capacity: int,
        refill_rate: float,
        tokens: int = 1,
    ) -> bool:
        bucket_key = f"{self.key_prefix}:{org_id}"
        result = self._script(
            keys=[bucket_key],
            args=[
                max(1, int(capacity)),
                max(0.0, float(refill_rate)),
                time.time(),
                max(1, int(tokens)),
                int(self.ttl_seconds),
            ],
        )
        return int(result) == 1


__all__ = ["RedisTokenBucketLimiter", "TOKEN_BUCKET_LUA"]
