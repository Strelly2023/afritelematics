"""Redis-backed runtime governance enforcement for partner traffic."""

from __future__ import annotations

from typing import Any
import os

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

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
        redis_client: Any | None = None,
        breaker_client: Any | None = None,
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

        limiter_client = redis_client
        breaker_backend = breaker_client if breaker_client is not None else redis_client

        self.rate_limiter = (
            RedisTokenBucketLimiter(client=limiter_client)
            if limiter_client is not None
            else RedisTokenBucketLimiter.from_url(redis_url or os.environ.get("REDIS_URL"))
        )
        self.circuit_breaker = (
            RedisCircuitBreaker(client=breaker_backend)
            if breaker_backend is not None
            else RedisCircuitBreaker.from_url(redis_url or os.environ.get("REDIS_URL"), recovery_seconds=self.recovery_seconds)
        )

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
        capacity = int(capacity_value) if capacity_value is not None else self.default_bucket_capacity
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

        return response


__all__ = ["DistributedGovernanceMiddleware"]
