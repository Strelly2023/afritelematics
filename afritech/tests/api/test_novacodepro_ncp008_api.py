from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_ncp008_api import build_novacodepro_ncp008_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    platform = NovaCodeProPlatform(repository)
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_ncp008_router(platform))
    return TestClient(app)


def _headers(tenant: str = "novatech", user_id: str = "platform-admin") -> dict[str, str]:
    token = JWT.create_token(
        user_id,
        role="ADMIN",
        organization_id=tenant,
        tenant_id=tenant,
        permissions=(
            "operations.read",
            "operations.workspace.read",
            "operations.environment.read",
            "operations.service.read",
            "operations.alert.read",
            "operations.alert.acknowledge",
            "operations.incident.read",
            "operations.incident.manage",
            "operations.timeline.write",
            "operations.action.request",
            "operations.action.approve",
            "operations.action.execute",
            "operations.action.verify",
            "operations.deployment.rollback",
            "operations.recovery.manage",
            "operations.postmortem.write",
        ),
    )
    return {"Authorization": f"Bearer {token}"}


def test_ncp008_api_supports_governed_operations_workflow(tmp_path: Path) -> None:
    client = _client(tmp_path)

    guard = client.get("/api/v1/operations/overview")
    assert guard.status_code == 401
    assert guard.headers["content-type"].startswith("application/json")

    headers = _headers()

    environment = client.post(
        "/api/v1/operations/environments",
        headers=headers,
        json={"code": "production", "name": "Production", "type": "PRODUCTION", "region": "Australia", "status": "ACTIVE"},
    )
    assert environment.status_code == 200
    environment_id = environment.json()["id"]

    service = client.post(
        "/api/v1/operations/services",
        headers=headers,
        json={
            "name": "Payments API",
            "environment_id": environment_id,
            "health_status": "HEALTHY",
            "readiness_status": "HEALTHY",
            "deployment_status": "ACTIVE",
            "criticality": "MISSION_CRITICAL",
            "dependencies": [],
            "endpoints": [],
        },
    )
    assert service.status_code == 200
    service_id = service.json()["id"]

    workspace = client.post(
        "/api/v1/operations/workspaces",
        headers=headers,
        json={"name": "Operations Workspace", "environment_ids": [environment_id], "service_ids": [service_id], "region_ids": ["AU"]},
    )
    assert workspace.status_code == 200

    overview = client.get("/api/v1/operations/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["service_count"] >= 1

    alert = client.post(
        "/api/v1/operations/alerts",
        headers=headers,
        json={"title": "Latency spike", "description": "p95 latency above threshold", "severity": "CRITICAL", "environment_id": environment_id, "service_id": service_id},
    )
    assert alert.status_code == 200
    alert_id = alert.json()["id"]
    assert client.post(f"/api/v1/operations/alerts/{alert_id}/acknowledge", headers=headers, json={"reason": "Investigating"}).status_code == 200

    incident = client.post(
        f"/api/v1/operations/alerts/{alert_id}/incident",
        headers=headers,
        json={"title": "Production latency incident", "severity": "SEV1", "type": "PERFORMANCE"},
    )
    assert incident.status_code == 200
    incident_id = incident.json()["id"]

    transitioned = client.post(f"/api/v1/operations/incidents/{incident_id}/transition", headers=headers, json={"status": "INVESTIGATING"})
    assert transitioned.status_code == 200
    assert client.post(f"/api/v1/operations/incidents/{incident_id}/timeline", headers=headers, json={"event_type": "NOTE", "title": "Checked ingress", "description": "Latency on ingress"}).status_code == 200

    action = client.post(
        "/api/v1/operations/actions",
        headers=headers,
        json={
            "action_type": "service_restart",
            "service_id": service_id,
            "environment_id": environment_id,
            "reason": "Controlled restart",
            "requested_parameters": {"window": "now"},
        },
    )
    assert action.status_code == 200
    action_id = action.json()["id"]
    duplicate = client.post(
        "/api/v1/operations/actions",
        headers={**headers, "Idempotency-Key": "action-dup"},
        json={
            "action_type": "service_restart",
            "service_id": service_id,
            "environment_id": environment_id,
            "reason": "Controlled restart",
            "requested_parameters": {"window": "now"},
        },
    )
    assert duplicate.status_code == 200
    assert client.post(f"/api/v1/operations/actions/{action_id}/approval-requests", headers=headers).status_code == 200
    approver_headers = _headers(user_id="platform-approver")
    assert client.post(f"/api/v1/operations/actions/{action_id}/approve", headers=approver_headers, json={"reason": "Approved"}).status_code == 200
    assert client.post(f"/api/v1/operations/actions/{action_id}/execute", headers=headers).status_code == 200
    assert client.post(f"/api/v1/operations/actions/{action_id}/verify", headers=headers).status_code == 200

    slo = client.post(
        "/api/v1/operations/slos",
        headers=headers,
        json={"name": "Availability SLO", "service_id": service_id, "environment_id": environment_id, "objective_type": "AVAILABILITY", "target": 0.999, "window": "30d"},
    )
    assert slo.status_code == 200
    slo_id = slo.json()["id"]
    assert client.post(f"/api/v1/operations/slos/{slo_id}/evaluate", headers=headers).status_code == 200

    recovery = client.post(
        "/api/v1/operations/recovery-plans",
        headers=headers,
        json={"name": "Payments recovery", "environment_id": environment_id, "service_id": service_id, "steps": ["Notify", "Restart"], "rollback_steps": ["Stop"], "required_approvals": ["operations.action.approve"], "validation_steps": ["Health check"]},
    )
    assert recovery.status_code == 200
    recovery_id = recovery.json()["id"]
    assert client.post(f"/api/v1/operations/recovery-plans/{recovery_id}/validate", headers=headers).status_code == 200

    review = client.post(
        f"/api/v1/operations/incidents/{incident_id}/post-incident-reviews",
        headers=headers,
        json={"summary": "Reviewed", "owners": ["ops"], "due_dates": {"ops": "2026-08-01"}},
    )
    assert review.status_code == 200
    review_id = review.json()["id"]
    assert client.post(f"/api/v1/operations/post-incident-reviews/{review_id}/publish", headers=headers).status_code == 200

    cross_tenant = client.get("/api/v1/operations/workspaces", headers=_headers("other-tenant", "other-admin"))
    assert cross_tenant.status_code in {200, 403}
    if cross_tenant.status_code == 200:
        assert all(workspace_item["tenant_id"] == "other-tenant" for workspace_item in cross_tenant.json()["workspaces"])


def test_ncp008_openapi_operation_ids_are_unique(tmp_path: Path) -> None:
    client = _client(tmp_path)
    schema = client.app.openapi()
    operation_ids = []
    for path, methods in schema["paths"].items():
        if not path.startswith("/api/v1/operations"):
            continue
        for method in methods.values():
            operation_ids.append(method["operationId"])
    assert len(operation_ids) == len(set(operation_ids))
