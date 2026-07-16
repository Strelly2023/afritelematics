"""Simple rate limit policy support."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from .errors import ApiPlatformError


@dataclass
class RateLimitBucket:
    limit: int
    window_seconds: int
    hits: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        now = monotonic()
        self.hits = [hit for hit in self.hits if now - hit <= self.window_seconds]
        if len(self.hits) >= self.limit:
            return False
        self.hits.append(now)
        return True


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, RateLimitBucket] = {}

    def configure(self, policy_name: str, *, limit: int, window_seconds: int) -> None:
        self._buckets[policy_name] = RateLimitBucket(limit=limit, window_seconds=window_seconds)

    def enforce(self, policy_name: str) -> None:
        bucket = self._buckets.get(policy_name)
        if bucket is None:
            return
        if not bucket.allow():
            raise ApiPlatformError("rate_limit_exceeded", code="API_RATE_LIMIT_EXCEEDED")
