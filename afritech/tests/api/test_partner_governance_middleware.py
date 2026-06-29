from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.partner_governance_api import build_partner_governance_router
from afritech.middleware.governance_middleware import GovernanceMiddleware
from afritech.partner_governance import PartnerGovernanceStore, seed_partner_governance_registry


def auth_headers(role: str = "VERIFIER", user_id: str = "verifier-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def build_client(
    *,
    bucket_capacity: int = 1,
    bucket_refill_rate: float = 0.0,
    failure_threshold: int = 1,
    recovery_time: float = 0.0,
) -> tuple[TestClient, PartnerGovernanceStore]:
    store = PartnerGovernanceStore(seed_partner_governance_registry())
    app = FastAPI()
    app.state.governance_store = store
    app.include_router(build_auth_router())
    app.include_router(build_partner_governance_router(store=store))
    app.add_middleware(
        GovernanceMiddleware,
        store=store,
        protected_paths=("/v1/trust/orgs",),
        default_bucket_capacity=bucket_capacity,
        default_bucket_refill_rate=bucket_refill_rate,
        failure_threshold=failure_threshold,
        recovery_time=recovery_time,
    )

    router = APIRouter()

    @router.get("/v1/trust/orgs/{org_id}/fail")
    def fail_endpoint(org_id: str) -> JSONResponse:
        return JSONResponse(status_code=500, content={"org_id": org_id, "status": "failed"})

    app.include_router(router)
    return TestClient(app), store


def test_governance_middleware_requires_org_id_header() -> None:
    client, _ = build_client(bucket_capacity=1)

    response = client.get(
        "/v1/trust/orgs/partner-city-ops",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_ORG_ID"


def test_governance_middleware_blocks_disabled_sla() -> None:
    client, store = build_client(bucket_capacity=1)
    store._replace("partner-city-ops", enforcement_state="disabled")

    response = client.get(
        "/v1/trust/orgs/partner-city-ops",
        headers={**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SLA_REVOKED"


def test_governance_middleware_rate_limits_per_org() -> None:
    client, _ = build_client(bucket_capacity=1)
    headers = {**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"}

    first = client.get("/v1/trust/orgs/partner-city-ops", headers=headers)
    second = client.get("/v1/trust/orgs/partner-city-ops", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_governance_middleware_opens_circuit_after_failure() -> None:
    client, _ = build_client(bucket_capacity=2, recovery_time=60.0)
    headers = {**auth_headers(role="OBSERVER"), "X-Org-ID": "partner-city-ops"}

    first = client.get("/v1/trust/orgs/partner-city-ops/fail", headers=headers)
    second = client.get("/v1/trust/orgs/partner-city-ops/fail", headers=headers)

    assert first.status_code == 500
    assert second.status_code == 503
    assert second.json()["error"]["code"] == "CIRCUIT_OPEN"
