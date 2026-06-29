"""Runtime governance enforcement for partner-facing routes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from afritech.middleware.circuit_breaker import CircuitBreaker
from afritech.middleware.rate_limiter import TokenBucket
from afritech.partner_governance import PartnerGovernanceStore


class GovernanceMiddleware(BaseHTTPMiddleware):
    """Enforce partner SLA, rate limits, and circuit-breaking at runtime."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        store: PartnerGovernanceStore,
        protected_paths: tuple[str, ...] | None = None,
        default_bucket_capacity: int = 1_000,
        default_bucket_refill_rate: float = 20.0,
        throttled_bucket_fraction: float = 0.1,
        failure_threshold: int = 5,
        recovery_time: float = 30.0,
    ) -> None:
        super().__init__(app)
        self.store = store
        self.protected_paths = protected_paths or ("/v1/trust/orgs", "/v1/partners")
        self.default_bucket_capacity = max(1, int(default_bucket_capacity))
        self.default_bucket_refill_rate = max(0.0, float(default_bucket_refill_rate))
        self.throttled_bucket_fraction = max(0.0, min(1.0, float(throttled_bucket_fraction)))
        self.failure_threshold = max(1, int(failure_threshold))
        self.recovery_time = max(0.0, float(recovery_time))
        self._buckets: dict[str, TokenBucket] = {}
        self._breakers: dict[str, CircuitBreaker] = {}

    def _bucket_for(self, org_id: str, *, throttled: bool) -> TokenBucket:
        bucket = self._buckets.get(org_id)
        if bucket is None:
            bucket = TokenBucket(
                self.default_bucket_capacity,
                self.default_bucket_refill_rate,
            )
            self._buckets[org_id] = bucket
        if throttled:
            bucket.configure(
                capacity=max(1, int(self.default_bucket_capacity * self.throttled_bucket_fraction)),
                refill_rate=max(0.0, self.default_bucket_refill_rate * self.throttled_bucket_fraction),
            )
        else:
            bucket.configure(
                capacity=self.default_bucket_capacity,
                refill_rate=self.default_bucket_refill_rate,
            )
        return bucket

    def _breaker_for(self, org_id: str) -> CircuitBreaker:
        breaker = self._breakers.get(org_id)
        if breaker is None:
            breaker = CircuitBreaker(
                failure_threshold=self.failure_threshold,
                recovery_time=self.recovery_time,
            )
            self._breakers[org_id] = breaker
        return breaker

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

        bucket = self._bucket_for(org_id, throttled=record.enforcement_state == "throttled")
        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "partner request quota exceeded",
                    }
                },
            )

        breaker = self._breaker_for(org_id)
        if not breaker.allow_request():
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "CIRCUIT_OPEN",
                        "message": "service temporarily unavailable",
                    }
                },
            )

        try:
            response = await call_next(request)
        except Exception:
            breaker.record_failure()
            raise

        if response.status_code >= 500:
            breaker.record_failure()
        else:
            breaker.reset()

        return response


__all__ = ["GovernanceMiddleware"]
