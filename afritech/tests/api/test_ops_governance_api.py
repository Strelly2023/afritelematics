from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.architecture_proof_api import build_architecture_proof_router
from afritech.api.ops_governance_api import build_ops_governance_router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_ops_governance_router())
    app.include_router(build_architecture_proof_router())
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "operator-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_ops_observability_dashboard_is_replay_linked() -> None:
    client = build_client()

    response = client.get(
        "/v1/ops/observability/dashboard",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "ops_observability_dashboard"
    assert payload["authority_boundary"] == "observability_explains_trace_and_replay_only"
    assert payload["alerts"]


def test_ops_audit_dashboard_is_enterprise_review_ready() -> None:
    client = build_client()

    response = client.get(
        "/v1/ops/audit/dashboard",
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "ops_audit_dashboard"
    assert payload["readiness"] == "ENTERPRISE_REVIEW_READY"
    assert payload["audit_exports"]["legal_proof_bundle_ready"] is True


def test_ops_system_integrity_dashboard_is_externally_verifiable() -> None:
    client = build_client()

    response = client.get(
        "/v1/system/integrity/dashboard",
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "system_integrity_dashboard"
    assert payload["proof_surface"]["anchor_id"].startswith("anchor-")
    assert payload["audit"]["controlled_live_demo_ready"] is True
