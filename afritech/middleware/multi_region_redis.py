"""Region-aware Redis backend selection for active-active trust enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Iterable
import os

try:  # pragma: no cover - dependency availability is environment-specific
    import redis  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for test/runtime environments
    redis = None


def parse_region_redis_urls(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    mapping: dict[str, str] = {}
    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            continue
        if "=" not in item:
            continue
        region, url = item.split("=", 1)
        region_key = region.strip().upper()
        url_value = url.strip()
        if region_key and url_value:
            mapping[region_key] = url_value
    return mapping


def build_region_weights(weights: dict[str, float] | None = None) -> dict[str, float]:
    merged = {"AU": 0.4, "EU": 0.3, "US": 0.3}
    if weights:
        for region, value in weights.items():
            merged[str(region).upper()] = max(0.0, float(value))
    total = sum(merged.values())
    if total <= 0:
        return {"AU": 1.0}
    return {region: value / total for region, value in merged.items()}


def regional_capacity(global_limit: int, region: str, weights: dict[str, float] | None = None) -> int:
    normalized_region = str(region or "").strip().upper()
    resolved_weights = build_region_weights(weights)
    fraction = resolved_weights.get(normalized_region)
    if fraction is None:
        fraction = 1.0 / max(1, len(resolved_weights))
    return max(1, int(round(int(global_limit) * fraction)))


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


@dataclass
class _RegionClient:
    region: str
    client: Any
    scripts: dict[str, Any] = field(default_factory=dict)


@dataclass
class RegionAwareRedisBackend:
    """Redis client proxy with region-aware failover and stable script binding."""

    region: str
    region_urls: dict[str, str]
    region_clients: dict[str, Any] | None = None
    fallback_order: tuple[str, ...] = ("AU", "EU", "US")
    fallback_client: Any | None = None
    _clients: dict[str, _RegionClient] = field(default_factory=dict, init=False, repr=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    @classmethod
    def from_env(
        cls,
        *,
        region: str | None = None,
        region_urls: dict[str, str] | None = None,
        fallback_order: Iterable[str] | None = None,
    ) -> "RegionAwareRedisBackend":
        resolved_region = str(
            region
            or os.environ.get("AFRITECH_TRUST_REGION")
            or os.environ.get("AFRITECH_REGION")
            or "AU"
        ).upper()
        resolved_urls = dict(region_urls or parse_region_redis_urls(os.environ.get("AFRITECH_TRUST_REDIS_URLS")))
        order = tuple(str(item).upper() for item in (fallback_order or ("AU", "EU", "US")))
        return cls(region=resolved_region, region_urls=resolved_urls, fallback_order=order)

    @classmethod
    def from_single_client(cls, client: Any, *, region: str = "AU") -> "RegionAwareRedisBackend":
        return cls(region=str(region).upper(), region_urls={}, region_clients={str(region).upper(): client})

    @classmethod
    def from_clients(
        cls,
        region_clients: dict[str, Any],
        *,
        region: str = "AU",
        region_urls: dict[str, str] | None = None,
        fallback_order: Iterable[str] | None = None,
    ) -> "RegionAwareRedisBackend":
        normalized_clients = {str(region_key).upper(): client for region_key, client in region_clients.items()}
        return cls(
            region=str(region).upper(),
            region_urls=dict(region_urls or {}),
            region_clients=normalized_clients,
            fallback_order=tuple(str(item).upper() for item in (fallback_order or ("AU", "EU", "US"))),
        )

    def _build_client(self, region: str) -> Any:
        if self.region_clients and region in self.region_clients:
            return self.region_clients[region]
        if self.fallback_client is not None:
            return self.fallback_client
        url = self.region_urls.get(region)
        if url and redis is not None:
            return redis.Redis.from_url(url)
        return _FallbackRedisClient()

    def _ordered_regions(self) -> tuple[str, ...]:
        preferred = [self.region] if self.region else []
        ordered: list[str] = []
        for region in preferred + list(self.fallback_order) + list(self.region_urls.keys()):
            normalized = str(region).upper()
            if normalized not in ordered:
                ordered.append(normalized)
        return tuple(ordered or ("AU",))

    def _client_for(self, region: str) -> _RegionClient:
        normalized = str(region).upper()
        with self._lock:
            cached = self._clients.get(normalized)
            if cached is not None:
                return cached
            client = self._build_client(normalized)
            entry = _RegionClient(region=normalized, client=client)
            self._clients[normalized] = entry
            return entry

    def _ordered_client_entries(self) -> tuple[_RegionClient, ...]:
        return tuple(self._client_for(region) for region in self._ordered_regions())

    def _with_failover(self, operation: Callable[[Any], Any]) -> Any:
        last_error: Exception | None = None
        for entry in self._ordered_client_entries():
            try:
                return operation(entry.client)
            except Exception as exc:  # pragma: no cover - exercised via failover tests
                last_error = exc
                with self._lock:
                    self._clients.pop(entry.region, None)
                continue
        if last_error is not None:
            raise last_error
        raise RuntimeError("no_redis_available")

    def register_script(self, script: str):
        def runner(*, keys, args):
            last_error: Exception | None = None
            for entry in self._ordered_client_entries():
                try:
                    with self._lock:
                        script_runner = entry.scripts.get(script)
                        if script_runner is None:
                            script_runner = entry.client.register_script(script)
                            entry.scripts[script] = script_runner
                    return script_runner(keys=keys, args=args)
                except Exception as exc:  # pragma: no cover - exercised via failover tests
                    last_error = exc
                    with self._lock:
                        self._clients.pop(entry.region, None)
                    continue
            if last_error is not None:
                raise last_error
            raise RuntimeError("no_redis_available")

        return runner

    def incr(self, key: str) -> int:
        return int(self._with_failover(lambda client: client.incr(key)))

    def expire(self, key: str, ttl: int) -> None:
        self._with_failover(lambda client: client.expire(key, ttl))

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._with_failover(lambda client: client.set(key, value, ex=ex))

    def get(self, key: str):
        return self._with_failover(lambda client: client.get(key))

    def delete(self, *keys: str) -> None:
        self._with_failover(lambda client: client.delete(*keys))


__all__ = [
    "RegionAwareRedisBackend",
    "build_region_weights",
    "parse_region_redis_urls",
    "regional_capacity",
]
