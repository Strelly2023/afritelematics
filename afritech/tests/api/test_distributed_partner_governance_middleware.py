from __future__ import annotations

from dataclasses import dataclass, field
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.partner_governance_api import build_partner_governance_router
from afritech.middleware.distributed_governance import DistributedGovernanceMiddleware
from afritech.partner_governance import PartnerGovernanceStore, seed_partner_governance_registry


def auth_headers(role: str = "VERIFIER", user_id: str = "verifier-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@dataclass
class FakeRedis:
    hashes: dict[str, dict[str, float]] = field(default_factory=dict)
    strings: dict[str, str] = field(default_factory=dict)

    def register_script(self, script: str):
        def runner(*, keys, args):
            key = keys[0]
            capacity, refill_rate, now, requested, ttl = args
            bucket = self.hashes.setdefault(key, {})
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
        value = int(float(self.strings.get(key, "0"))) + 1
        self.strings[key] = str(value)
        return value

    def expire(self, key: str, ttl: int) -> None:  # noqa: ARG002
        return None

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.strings[key] = str(value)

    def get(self, key: str):
        return self.strings.get(key)

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.strings.pop(key, None)
            self.hashes.pop(key, None)


def build_client(
    *,
    shared_redis: FakeRedis | None = None,
    store: PartnerGovernanceStore | None = None,
    failure_threshold: int = 5,
    recovery_seconds: int = 60,
    request_limit_per_min: int | None = None,
) -> tuple[TestClient, PartnerGovernanceStore, FakeRedis]:
    store = store or PartnerGovernanceStore(seed_partner_governance_registry())
    if request_limit_per_min is not None:
        current = store.load("partner-city-ops")
        limits = dict(current.limits)
        limits["requests_per_min"] = int(request_limit_per_min)
        store._replace("partner-city-ops", limits=limits)
    redis_backend = shared_redis or FakeRedis()
    app = FastAPI()
    app.state.governance_store = store
    app.include_router(build_auth_router())
    app.include_router(build_partner_governance_router(store=store))
    app.add_middleware(
        DistributedGovernanceMiddleware,
        store=store,
        redis_client=redis_backend,
        breaker_client=redis_backend,
        failure_threshold=failure_threshold,
        recovery_seconds=recovery_seconds,
    )

    router = APIRouter()

    @router.get("/v1/trust/orgs/{org_id}/fail")
    def fail_endpoint(org_id: str) -> JSONResponse:
        return JSONResponse(status_code=500, content={"org_id": org_id, "status": "failed"})

    app.include_router(router)
    return TestClient(app), store, redis_backend


def test_distributed_governance_requires_org_id_header() -> None:
    client, _, _ = build_client()

    response = client.get(
        "/v1/trust/orgs/partner-city-ops",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_ORG_ID"


def test_distributed_governance_blocks_disabled_sla() -> None:
    client, store, _ = build_client()
    store._replace("partner-city-ops", enforcement_state="disabled")

    response = client.get(
        "/v1/trust/orgs/partner-city-ops",
        headers={**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SLA_REVOKED"


def test_distributed_governance_rate_limit_is_shared_across_instances() -> None:
    shared_redis = FakeRedis()
    shared_store = PartnerGovernanceStore(seed_partner_governance_registry())
    client_a, _, _ = build_client(
        shared_redis=shared_redis,
        store=shared_store,
        request_limit_per_min=1,
    )
    client_b, _, _ = build_client(
        shared_redis=shared_redis,
        store=shared_store,
        request_limit_per_min=1,
    )
    headers = {**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"}

    response = None
    for index in range(101):
        client = client_a if index % 2 == 0 else client_b
        response = client.get("/v1/trust/orgs/partner-city-ops", headers=headers)

    assert response is not None
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_distributed_governance_opens_shared_circuit() -> None:
    shared_redis = FakeRedis()
    client_a, _, _ = build_client(shared_redis=shared_redis, failure_threshold=1, recovery_seconds=60)
    client_b, _, _ = build_client(shared_redis=shared_redis, failure_threshold=1, recovery_seconds=60)
    headers = {**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"}

    first = client_a.get("/v1/trust/orgs/partner-city-ops/fail", headers=headers)
    second = client_b.get("/v1/trust/orgs/partner-city-ops/fail", headers=headers)

    assert first.status_code == 500
    assert second.status_code == 503
    assert second.json()["error"]["code"] == "CIRCUIT_OPEN"
