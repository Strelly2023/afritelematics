from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    app.include_router(build_novacodepro_session_router())
    return TestClient(app)


def _login(client: TestClient, role: str = "PRODUCT_MANAGER") -> None:
    response = client.post(
        "/v1/novacodepro/session/login",
        json={"email": "productmanager.test@afritechnology.com", "password": "NovaCodePro123!", "role": role},
    )
    assert response.status_code == 200


def _bearer(role: str, user_id: str, organization_id: str = "novatech", workspace_id: str | None = None) -> dict[str, str]:
    token = JWT.create_token(
        user_id,
        role=role,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permissions=(
            "requirements.read",
            "requirements.create",
            "requirements.update",
            "requirements.review",
            "requirements.baseline",
            "traceability.read",
            "traceability.manage",
            "knowledge.read",
            "knowledge.create",
            "knowledge.update",
            "knowledge.review",
            "knowledge.approve",
            "knowledge.publish",
            "knowledge.search",
        ),
    )
    return {"Authorization": f"Bearer {token}"}


def test_ncp005_requirements_state_machine_and_traceability(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _login(client)

    workspace_id = client.get("/v1/novacodepro/workspaces").json()["workspaces"][0]["id"]
    selected = client.post(f"/v1/novacodepro/workspaces/{workspace_id}/select")
    assert selected.status_code == 200

    requirement_set = client.post("/v1/novacodepro/requirement-sets", json={"name": "Pilot requirements"})
    assert requirement_set.status_code == 200
    requirement_set_id = requirement_set.json()["id"]

    requirement = client.post(
        "/v1/novacodepro/requirements",
        headers={"Idempotency-Key": "ncp005-requirement"},
        json={
            "workspace_id": workspace_id,
            "project_id": "nova-ride-platform",
            "request_id": "req-123",
            "set_id": requirement_set_id,
            "title": "Rider registration",
            "summary": "Build rider registration with NovaID identity verification",
            "type": "FUNCTIONAL",
            "priority": "HIGH",
            "source": "REQUEST",
            "content": {"details": "secure registration"},
        },
    )
    assert requirement.status_code == 200
    requirement_id = requirement.json()["id"]

    review = client.post(f"/v1/novacodepro/requirements/{requirement_id}/reviews", json={"review_type": "PRODUCT"})
    assert review.status_code == 200

    approval_request = client.post(f"/v1/novacodepro/requirements/{requirement_id}/approvals", json={"required_role": "PRODUCT_MANAGER"})
    assert approval_request.status_code == 200
    approval_id = approval_request.json()["id"]

    approval = client.post(f"/v1/novacodepro/requirements/{requirement_id}/approvals/{approval_id}/approve", json={"reason": "Looks good"})
    assert approval.status_code == 200
    assert approval.json()["decision"] == "APPROVED"

    baselined = client.post(f"/v1/novacodepro/requirements/{requirement_id}/transition", json={"status": "BASELINED", "reason": "baseline"})
    assert baselined.status_code == 200
    assert baselined.json()["status"] == "BASELINED"

    criterion = client.post(
        f"/v1/novacodepro/requirements/{requirement_id}/acceptance-criteria",
        json={"description": "Given a valid NovaID account, when registration completes, then a verified rider profile exists.", "criterion_type": "GIVEN_WHEN_THEN"},
    )
    assert criterion.status_code == 200

    link = client.post(
        "/v1/novacodepro/traceability/links",
        json={
            "source_type": "REQUIREMENT",
            "source_id": requirement_id,
            "target_type": "TEST_CASE",
            "target_id": "test-case-1",
            "relationship": "VERIFIES",
        },
    )
    assert link.status_code == 200

    coverage = client.get("/v1/novacodepro/traceability/coverage")
    assert coverage.status_code == 200
    assert coverage.json()["coverage"]["coverage_ratio"] >= 0

    implementing = client.post(f"/v1/novacodepro/requirements/{requirement_id}/transition", json={"status": "IMPLEMENTING", "reason": "implementation started"})
    assert implementing.status_code == 200

    verified = client.post(f"/v1/novacodepro/requirements/{requirement_id}/transition", json={"status": "VERIFIED", "reason": "verification complete"})
    assert verified.status_code == 200

    archived = client.post(f"/v1/novacodepro/requirements/{requirement_id}/archive")
    assert archived.status_code == 200

    forbidden = client.post(
        "/v1/novacodepro/requirements",
        headers=_bearer("CUSTOMER", "customer.user", workspace_id=workspace_id),
        json={"workspace_id": workspace_id, "project_id": "nova-ride-platform", "title": "Forbidden requirement"},
    )
    assert forbidden.status_code in {401, 403}
