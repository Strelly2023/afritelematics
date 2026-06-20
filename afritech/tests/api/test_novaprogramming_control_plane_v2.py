from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import (
    build_afriprogramming_control_router,
)


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afriprogramming_control_router())
    return TestClient(app)


def auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_proofs_are_organization_scoped() -> None:
    client = build_client()
    organization_id = f"org-{uuid4().hex[:8]}"

    proof = client.post(
        "/v1/novaprogramming/verify/generate-proof",
        json={
            "execution_id": "execution-v2-001",
            "project_id": "project-employee-rbac",
            "payload": {"surface": "studio"},
        },
        headers=auth_headers("VERIFIER", "verifier-v2", organization_id),
    )
    assert proof.status_code == 200

    allowed = client.get(
        "/v1/novaprogramming/verify/execution-v2-001",
        headers=auth_headers("OBSERVER", "observer-v2", organization_id),
    )
    assert allowed.status_code == 200

    denied = client.get(
        "/v1/novaprogramming/verify/execution-v2-001",
        headers=auth_headers("OBSERVER", "observer-other", f"{organization_id}-other"),
    )
    assert denied.status_code == 404


def test_insights_track_organization_activity() -> None:
    client = build_client()
    organization_id = f"org-{uuid4().hex[:8]}"

    request = client.post(
        "/v1/novaprogramming/cloud/request-deploy",
        json={
            "service": "api",
            "environment": "production",
            "image": "nova-programming:latest",
            "rationale": "go-live",
        },
        headers=auth_headers("OPERATOR", "operator-v2", organization_id),
    )
    assert request.status_code == 200

    insights = client.get(
        "/v1/novaprogramming/insights",
        headers=auth_headers("OBSERVER", "observer-v2", organization_id),
    )
    assert insights.status_code == 200
    body = insights.json()
    assert body["organization_id"] == organization_id
    assert body["deployment_requests"] >= 1
    assert body["risk_score"] <= 100
