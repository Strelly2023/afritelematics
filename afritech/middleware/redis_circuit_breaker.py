"""Redis-backed circuit breaker for distributed partner enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any
import os
import time

try:  # pragma: no cover - dependency availability is environment-specific
    import redis  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for test/runtime environments
    redis = None


class _FallbackRedisClient:
    def __init__(self) -> None:
        self._strings: dict[str, str] = {}
        self._lock = Lock()

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


_FALLBACK_REDIS_CLIENT = _FallbackRedisClient()


@dataclass
class RedisCircuitBreaker:
    client: Any
    key_prefix: str = "governance:circuit"
    recovery_seconds: int = 60

    @classmethod
    def from_url(
        cls,
        redis_url: str | None = None,
        *,
        key_prefix: str = "governance:circuit",
        recovery_seconds: int = 60,
    ) -> "RedisCircuitBreaker":
        if redis is None:
            client = _FALLBACK_REDIS_CLIENT
        else:
            client = redis.Redis.from_url(redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        return cls(client=client, key_prefix=key_prefix, recovery_seconds=recovery_seconds)

    def _failures_key(self, org_id: str) -> str:
        return f"{self.key_prefix}:{org_id}:failures"

    def _open_until_key(self, org_id: str) -> str:
        return f"{self.key_prefix}:{org_id}:open_until"

    def record_failure(self, org_id: str, *, threshold: int) -> None:
        failures_key = self._failures_key(org_id)
        failures = int(self.client.incr(failures_key))
        self.client.expire(failures_key, int(self.recovery_seconds))
        if failures >= max(1, int(threshold)):
            open_until = int(time.time()) + max(1, int(self.recovery_seconds))
            self.client.set(self._open_until_key(org_id), str(open_until), ex=int(self.recovery_seconds))

    def is_open(self, org_id: str) -> bool:
        open_until_value = self.client.get(self._open_until_key(org_id))
        if not open_until_value:
            return False
        try:
            open_until = int(open_until_value)
        except (TypeError, ValueError):
            return False
        now = int(time.time())
        if now < open_until:
            return True
        self.reset(org_id)
        return False

    def reset(self, org_id: str) -> None:
        self.client.delete(self._failures_key(org_id))
        self.client.delete(self._open_until_key(org_id))


__all__ = ["RedisCircuitBreaker"]
