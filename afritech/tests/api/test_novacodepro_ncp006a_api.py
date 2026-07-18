from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


ARCH_PERMS = (
    "architecture.read",
    "architecture.create",
    "architecture.update",
    "architecture.review",
    "architecture.approve",
    "architecture.baseline",
    "architecture.validate",
    "architecture.traceability",
)


def _client(tmp_path: Path) -> TestClient:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_novacodepro_platform_router(service))
    return TestClient(app)


def _headers(role: str = "ARCHITECT", user_id: str = "arch.user", organization_id: str = "novatech", workspace_id: str = "architecture-workspace") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id, workspace_id=workspace_id, permissions=ARCH_PERMS)
    return {"Authorization": f"Bearer {token}"}


def test_architecture_api_supports_governed_crud_and_validation(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _headers()

    workspace = client.post(
        "/v1/novacodepro/architecture/workspaces",
        headers=headers,
        json={"name": "Enterprise Architecture", "domain": "ENTERPRISE", "description": "Main architecture workspace"},
    )
    assert workspace.status_code == 200
    workspace_id = workspace.json()["id"]

    model = client.post(
        "/v1/novacodepro/architecture/models",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "name": "NovaCodePro Platform Architecture",
            "domain": "SOLUTION",
            "description": "Solution architecture for the governed platform",
            "technology_standard": "OpenAPI",
            "slo": {"availability": "99.9%"},
        },
    )
    assert model.status_code == 200
    model_id = model.json()["id"]

    component = client.post(
        "/v1/novacodepro/architecture/components",
        headers=headers,
        json={"model_id": model_id, "name": "API Gateway", "component_type": "GATEWAY", "technology": "Envoy"},
    )
    assert component.status_code == 200

    security = client.post(
        "/v1/novacodepro/architecture/security",
        headers=headers,
        json={
            "model_id": model_id,
            "threat_model": ["SPOOFING", "TAMPERING"],
            "security_controls": ["JWT validation", "tenant isolation"],
            "privacy_controls": ["data minimisation"],
        },
    )
    assert security.status_code == 200

    data = client.post(
        "/v1/novacodepro/architecture/data",
        headers=headers,
        json={
            "model_id": model_id,
            "classification": "CONFIDENTIAL",
            "retention": "retain-indefinitely",
            "logical_model": {"entities": ["Workspace", "Model"]},
        },
    )
    assert data.status_code == 200

    deployment = client.post(
        "/v1/novacodepro/architecture/deployments",
        headers=headers,
        json={"model_id": model_id, "environment": "PRODUCTION", "nodes": ["api-1"], "rto": "1h", "rpo": "15m"},
    )
    assert deployment.status_code == 200

    relationship = client.post(
        "/v1/novacodepro/architecture/relationships",
        headers=headers,
        json={"model_id": model_id, "source_id": model_id, "target_id": component.json()["id"], "relationship": "CONTAINS"},
    )
    assert relationship.status_code == 200

    review = client.post(
        "/v1/novacodepro/architecture/reviews",
        headers=headers,
        json={"model_id": model_id, "review_type": "ARCHITECTURE", "required_role": "ARCHITECT"},
    )
    assert review.status_code == 200
    review_id = review.json()["id"]

    review_complete = client.post(
        f"/v1/novacodepro/architecture/reviews/{review_id}/complete",
        headers=headers,
        json={"model_id": model_id, "decision": "APPROVED", "findings": ["Looks good"]},
    )
    assert review_complete.status_code == 200
    assert review_complete.json()["decision"] == "APPROVED"

    approval = client.post(
        "/v1/novacodepro/architecture/approvals",
        headers=headers,
        json={"model_id": model_id, "required_role": "ARCHITECT", "risk_class": "HIGH"},
    )
    assert approval.status_code == 200
    approval_id = approval.json()["id"]

    approved = client.post(
        f"/v1/novacodepro/architecture/approvals/{approval_id}/approve",
        headers=headers,
        json={"model_id": model_id, "reason": "Approved for pilot"},
    )
    assert approved.status_code == 200
    assert approved.json()["decision"] == "APPROVED"

    baseline = client.post(
        "/v1/novacodepro/architecture/baselines",
        headers=headers,
        json={"model_id": model_id, "name": "Baseline A", "approval_references": [approval_id]},
    )
    assert baseline.status_code == 200
    baseline_id = baseline.json()["id"]

    activated = client.post(
        f"/v1/novacodepro/architecture/baselines/{baseline_id}/activate?model_id={model_id}",
        headers=headers,
        json={},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "ACTIVE"

    validation = client.post(
        f"/v1/novacodepro/architecture/validation?model_id={model_id}",
        headers=headers,
        json={"validation_type": "POLICY"},
    )
    assert validation.status_code == 200
    assert validation.json()["status"] == "PASS"

    fitness = client.post(
        f"/v1/novacodepro/architecture/fitness?model_id={model_id}",
        headers=headers,
        json={},
    )
    assert fitness.status_code == 200
    assert fitness.json()["status"] in {"PASS", "FAIL"}

    diagram = client.post(
        f"/v1/novacodepro/architecture/diagrams?model_id={model_id}",
        headers=headers,
        json={"diagram_type": "SYSTEM_CONTEXT", "format": "JSON", "title": "Context"},
    )
    assert diagram.status_code == 200
    assert set(diagram.json()["exports"].keys()) == {"json", "mermaid", "plantuml", "svg", "png"}

    impact = client.post(f"/v1/novacodepro/architecture/impact?model_id={model_id}", headers=headers, json={})
    assert impact.status_code == 200
    assert impact.json()["status"] in {"ACTIVE", "NO_IMPACT"}

    versions = client.get(f"/v1/novacodepro/architecture/models/{model_id}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()["versions"]) >= 1


def test_architecture_api_rejects_cross_tenant_access_and_missing_traceability_sources(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _headers(role="DEVELOPER", user_id="arch.dev", organization_id="novatech", workspace_id="architecture-workspace")
    workspace = client.post("/v1/novacodepro/architecture/workspaces", headers=headers, json={"name": "Arch Workspace"})
    workspace_id = workspace.json()["id"]
    model = client.post(
        "/v1/novacodepro/architecture/models",
        headers=headers,
        json={"workspace_id": workspace_id, "name": "Architecture Model", "domain": "SOLUTION"},
    )
    model_id = model.json()["id"]

    forbidden = client.get(
        f"/v1/novacodepro/architecture/models/{model_id}",
        headers=_headers(role="ARCHITECT", user_id="other.user", organization_id="foreign-tenant", workspace_id="architecture-workspace"),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "cross_tenant_architecture_forbidden"

    missing = client.post(
        "/v1/novacodepro/architecture/approvals",
        headers=headers,
        json={"model_id": model_id, "required_role": "ARCHITECT", "risk_class": "MODERATE"},
    )
    assert missing.status_code == 200

    traceability_error = client.post(
        "/v1/novacodepro/architecture/components",
        headers=headers,
        json={"model_id": model_id, "name": "Bad component", "component_type": "GATEWAY", "technology": "Envoy", "metadata": {"traceability": "missing"}},
    )
    assert traceability_error.status_code == 200

    bad_link = client.post(
        f"/v1/novacodepro/architecture/validation?model_id={model_id}",
        headers=headers,
        json={"validation_type": "INVALID"},
    )
    assert bad_link.status_code == 400
    assert bad_link.json()["detail"]["code"] == "validation_failed"
