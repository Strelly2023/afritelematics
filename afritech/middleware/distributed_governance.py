"""Redis-backed runtime governance enforcement for partner traffic."""

from __future__ import annotations

from typing import Any
import os

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from afritech.middleware.multi_region_redis import (
    RegionAwareRedisBackend,
    regional_capacity,
)
from afritech.core_platform.geo_routing import adjust_sla_capacity, select_region
from afritech.core_platform.geo_routing import parse_latency_map, parse_region_health
from afritech.middleware.redis_circuit_breaker import RedisCircuitBreaker
from afritech.middleware.redis_rate_limiter import RedisTokenBucketLimiter
from afritech.partner_governance import PartnerGovernanceStore


class DistributedGovernanceMiddleware(BaseHTTPMiddleware):
    """Enforce partner SLA and operational health across all app instances."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        store: PartnerGovernanceStore,
        redis_url: str | None = None,
        redis_urls: dict[str, str] | None = None,
        region: str | None = None,
        redis_client: Any | None = None,
        breaker_client: Any | None = None,
        redis_backend: Any | None = None,
        protected_paths: tuple[str, ...] | None = None,
        default_bucket_capacity: int = 1_000,
        default_bucket_refill_rate: float = 20.0,
        throttled_bucket_fraction: float = 0.1,
        failure_threshold: int = 5,
        recovery_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.store = store
        self.protected_paths = protected_paths or ("/v1/trust/orgs", "/v1/partners")
        self.default_bucket_capacity = max(1, int(default_bucket_capacity))
        self.default_bucket_refill_rate = max(0.0, float(default_bucket_refill_rate))
        self.throttled_bucket_fraction = max(0.0, min(1.0, float(throttled_bucket_fraction)))
        self.failure_threshold = max(1, int(failure_threshold))
        self.recovery_seconds = max(1, int(recovery_seconds))
        self.region = str(region or os.environ.get("AFRITECH_TRUST_REGION") or os.environ.get("AFRITECH_REGION") or "AU").upper()
        self.region_weights = {"AU": 0.4, "EU": 0.3, "US": 0.3}

        if redis_backend is not None:
            backend = redis_backend
        elif redis_client is not None or breaker_client is not None:
            backend = redis_client if redis_client is not None else breaker_client
        else:
            backend = RegionAwareRedisBackend.from_env(
                region=self.region,
                region_urls=redis_urls,
            )

        self.rate_limiter = (
            RedisTokenBucketLimiter(client=backend)
        )
        self.circuit_breaker = (
            RedisCircuitBreaker(client=backend, recovery_seconds=self.recovery_seconds)
        )

    def _request_region(self, request: Request) -> str:
        for header_name in ("X-Edge-Region", "X-Target-Region", "X-Region", "X-Forwarded-Region"):
            value = str(request.headers.get(header_name) or "").strip()
            if value:
                return value.upper()
        return self.region

    def _request_country(self, request: Request) -> str | None:
        for header_name in ("CF-IPCountry", "X-Client-Country", "X-Country"):
            value = str(request.headers.get(header_name) or "").strip()
            if value:
                return value.upper()
        return None

    def _request_health_map(self, request: Request) -> dict[str, str]:
        return parse_region_health(request.headers.get("X-Region-Health"))

    def _request_latency_map(self, request: Request) -> dict[str, int]:
        return parse_latency_map(request.headers.get("X-Region-Latency-MS"))

    def _request_latency_ms(self, request: Request) -> int | None:
        for header_name in ("X-Edge-Latency-MS", "X-Client-Latency-MS"):
            value = str(request.headers.get(header_name) or "").strip()
            if not value:
                continue
            try:
                return max(0, int(float(value)))
            except ValueError:
                continue
        return None

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or not any(
            request.url.path.startswith(prefix) for prefix in self.protected_paths
        ):
            return await call_next(request)

        org_id = str(request.headers.get("X-Org-ID") or "").strip()
        if not org_id:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "MISSING_ORG_ID",
                        "message": "X-Org-ID header required",
                    }
                },
            )

        try:
            record = self.store.load(org_id)
        except KeyError:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "ORG_NOT_FOUND",
                        "message": "organization not found",
                    }
                },
            )

        if record.enforcement_state == "disabled":
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "SLA_REVOKED",
                        "message": "partner SLA enforcement disabled",
                    }
                },
            )

        if self.circuit_breaker.is_open(org_id):
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "CIRCUIT_OPEN",
                        "message": "service temporarily unavailable",
                    }
                },
            )

        capacity_value = record.limits.get("requests_per_min")
        global_capacity = int(capacity_value) if capacity_value is not None else self.default_bucket_capacity
        request_region = self._request_region(request)
        request_country = self._request_country(request)
        region_decision = select_region(
            client_country=request_country,
            client_region=request_region,
            preferred_region=request_region,
            trust_level=record.trust_level,
            health_map=self._request_health_map(request),
            latency_map=self._request_latency_map(request),
        )

        capacity = regional_capacity(global_capacity, region_decision["region"], self.region_weights)
        latency_ms = self._request_latency_ms(request)
        if latency_ms is None:
            latency_ms = region_decision.get("latency_ms")
        capacity = adjust_sla_capacity(capacity, latency_ms, record.trust_level)
        if record.enforcement_state == "throttled":
            capacity = max(1, int(capacity * self.throttled_bucket_fraction))
        refill_rate = max(0.0, float(capacity) / 60.0)
        if not self.rate_limiter.allow_request(org_id, capacity=capacity, refill_rate=refill_rate):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "partner request quota exceeded",
                    }
                },
            )

        try:
            response = await call_next(request)
        except Exception:
            self.circuit_breaker.record_failure(org_id, threshold=self.failure_threshold)
            raise

        if response.status_code >= 500:
            self.circuit_breaker.record_failure(org_id, threshold=self.failure_threshold)
        else:
            self.circuit_breaker.reset(org_id)

        request.state.geo_routing = region_decision
        request.state.sla_capacity = capacity
        request.state.edge_latency_ms = latency_ms

        return response


__all__ = ["DistributedGovernanceMiddleware"]
