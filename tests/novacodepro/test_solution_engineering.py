from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.api.solution_engineering_api import build_solution_engineering_router
from afritech.novacodepro.platform import NovaCodeProPlatform, NovaCodeProRepository
from afritech.novacodepro.solution_engineering import SolutionEngineeringService


def _service(db_path: Path) -> SolutionEngineeringService:
    platform = NovaCodeProPlatform(NovaCodeProRepository(db_path))
    return SolutionEngineeringService(platform)


def _client(service: SolutionEngineeringService) -> TestClient:
    app = FastAPI()
    app.include_router(build_solution_engineering_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str = "customer-owner", organization_id: str = "novatech", tenant_id: str = "novatech") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id, tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}


def test_customer_solution_lifecycle_and_gate_enforcement(tmp_path: Path) -> None:
    service = _service(tmp_path / "solution-engineering.sqlite3")
    client = _client(service)
    headers = _headers("ADMIN", organization_id="novatech", tenant_id="novatech")

    customer = client.post(
        "/v1/solution-engineering/customers",
        headers=headers,
        json={
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "name": "Acme Mobility",
            "segment": "enterprise",
            "country": "KE",
        },
    )
    assert customer.status_code == 200

    project = client.post(
        "/v1/solution-engineering/projects",
        headers=headers,
        json={
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "customer_id": customer.json()["id"],
            "name": "Multilingual commerce platform",
            "idea": "Build a multilingual ecommerce platform for East Africa.",
        },
    )
    assert project.status_code == 200
    project_id = project.json()["id"]

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/idea", headers=_headers("CUSTOMER"), json={
        "title": "Multilingual commerce platform",
        "problem": "Customers need a multilingual ecommerce platform.",
        "target_users": ["buyers", "sellers"],
        "market": "East Africa",
        "industry": "commerce",
    }).status_code == 200

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/discovery", headers=headers, json={
        "template": "enterprise",
        "discovery_summary": "Discovery complete",
        "objectives": ["Launch commerce", "Support multiple languages"],
        "stakeholders": ["Customer", "Operations"],
        "follow_up_questions": ["Which payment methods are required?"],
    }).status_code == 200

    requirement = client.post(
        f"/v1/solution-engineering/projects/{project_id}/requirements",
        headers=_headers("BUSINESS_ANALYST"),
        json={
            "summary": "Support checkout in English and Swahili.",
            "kind": "functional",
            "priority": "high",
            "acceptance_criteria": ["Language selectable", "Checkout strings localized"],
            "test_links": ["tests/e2e/test_checkout_localization.py"],
        },
    )
    assert requirement.status_code == 200

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/requirements/approve", headers=_headers("PRODUCT_MANAGER")).status_code == 200

    blueprint = client.post(
        f"/v1/solution-engineering/projects/{project_id}/blueprint",
        headers=_headers("ARCHITECT"),
        json={
            "executive_summary": "Solution blueprint for a multilingual ecommerce platform.",
            "scope": ["customer portal", "checkout", "payments"],
            "personas": [{"name": "Buyer"}],
            "product_surfaces": ["web", "mobile"],
            "feature_catalogue": ["catalogue", "checkout", "wallet"],
        },
    )
    assert blueprint.status_code == 200
    assert blueprint.json()["provenance"]["generator"] == "NovaCodePro Solution Engine"

    assert client.post(
        f"/v1/solution-engineering/projects/{project_id}/blueprint/sections",
        headers=_headers("ARCHITECT"),
        json={"section": "scope", "status": "APPROVED"},
    ).status_code == 200

    architecture = client.post(
        f"/v1/solution-engineering/projects/{project_id}/architecture",
        headers=_headers("ARCHITECT"),
        json={
            "decision": "Use NovaWorkflow Fabric for governed execution.",
            "requirements": [requirement.json()["id"]],
            "affected_services": ["NovaCodePro", "NovaWorkflow"],
            "tests": ["tests/novacodepro/test_solution_engineering.py"],
        },
    )
    assert architecture.status_code == 200

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/architecture/approve", headers=_headers("ARCHITECT")).status_code == 200
    assert client.post(f"/v1/solution-engineering/projects/{project_id}/designs", headers=_headers("UI_UX_DESIGNER"), json={
        "artifact_type": "wireframe",
        "surface": "web",
        "requirements": [requirement.json()["id"]],
        "prototype_links": ["https://example.invalid/prototype"],
    }).status_code == 200

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/plans", headers=_headers("PROJECT_MANAGER"), json={
        "objectives": ["Implement ecommerce flows"],
        "tasks": [{"id": "task-1", "title": "Scaffold app"}],
        "responsible_agents": ["Backend Developer Agent", "Frontend Developer Agent"],
        "required_approvals": ["architecture", "security", "customer"],
    }).status_code == 200

    assert client.post(f"/v1/solution-engineering/projects/{project_id}/implement", headers=_headers("DEVELOPER")).status_code == 200
    assert client.post(f"/v1/solution-engineering/projects/{project_id}/tests", headers=_headers("QA_ENGINEER"), json={"suite": "regression", "status": "PASS"}).status_code == 200
    assert client.post(f"/v1/solution-engineering/projects/{project_id}/security-review", headers=_headers("SECURITY_ENGINEER"), json={"status": "APPROVED"}).status_code == 200
    assert client.post(f"/v1/solution-engineering/projects/{project_id}/compliance-review", headers=_headers("PRIVACY_COMPLIANCE"), json={"status": "APPROVED"}).status_code == 200
    assert client.post(f"/v1/solution-engineering/projects/{project_id}/customer-review", headers=headers, json={"status": "APPROVED", "comments": ["Looks good"]}).status_code == 200

    release = client.post(
        f"/v1/solution-engineering/projects/{project_id}/release",
        headers=_headers("PROJECT_MANAGER"),
        json={"name": "Pilot release", "version": "1.0.0", "environment": "pilot", "scope": ["checkout"]},
    )
    assert release.status_code == 200
    release_id = release.json()["id"]

    blocked = client.post(
        f"/v1/solution-engineering/releases/{release_id}/deploy",
        headers=_headers("OPERATOR"),
        json={"environment": "pilot", "result": "blocked"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["code"] == "release_not_approved"

    assert client.post(f"/v1/solution-engineering/releases/{release_id}/approve", headers=_headers("OPERATOR")).status_code == 200
    deployment = client.post(
        f"/v1/solution-engineering/releases/{release_id}/deploy",
        headers=_headers("OPERATOR"),
        json={
            "environment": "pilot",
            "image_digest": "sha256:123",
            "migration_version": "0014",
            "artifact_refs": ["artifact-1"],
            "verification": {"smoke": "PASS"},
        },
    )
    assert deployment.status_code == 200
    accept = client.post(
        f"/v1/solution-engineering/releases/{release_id}/accept",
        headers=headers,
        json={"decision": "ACCEPTED", "evidence_hash": "abc123", "comments": ["Accepted"]},
    )
    assert accept.status_code == 200

    evidence = client.post(
        f"/v1/solution-engineering/projects/{project_id}/evidence",
        headers=_headers("ADMIN"),
        json={"category": "handover", "artifact_refs": [release_id], "notes": "handover evidence"},
    )
    assert evidence.status_code == 200
    assert len(evidence.json()["evidence_hash"]) == 64

    replay = client.get(f"/v1/solution-engineering/projects/{project_id}/timeline", headers=headers)
    assert replay.status_code == 200
    assert replay.json()["timeline"]

    dashboard = client.get("/v1/solution-engineering/studio", headers=headers)
    assert dashboard.status_code == 200
    assert "Customer Dashboard" in dashboard.text
    assert "Operations Layer" in dashboard.text


def test_solution_engineering_tenant_isolation_and_approval_boundaries(tmp_path: Path) -> None:
    service = _service(tmp_path / "solution-engineering-isolation.sqlite3")
    client = _client(service)

    project = client.post(
        "/v1/solution-engineering/projects",
        headers=_headers("ADMIN", organization_id="novatech", tenant_id="tenant-a"),
        json={
            "tenant_id": "tenant-a",
            "organization_id": "novatech",
            "name": "Tenant A project",
            "idea": "Project in tenant A",
        },
    )
    assert project.status_code == 200
    project_id = project.json()["id"]

    other_tenant = client.get(f"/v1/solution-engineering/projects/{project_id}", headers=_headers("CUSTOMER", organization_id="novatech", tenant_id="tenant-b"))
    assert other_tenant.status_code == 404

    forbidden = client.post(f"/v1/solution-engineering/projects/{project_id}/architecture/approve", headers=_headers("CUSTOMER", organization_id="novatech", tenant_id="tenant-a"))
    assert forbidden.status_code in {401, 403}


def test_solution_engineering_replay_survives_restart_and_retains_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "solution-engineering-replay.sqlite3"
    service = _service(db_path)
    project = service.create_project(
        {
            "tenant_id": "novatech",
            "organization_id": "novatech",
            "name": "Support portal",
            "idea": "Build a support portal for enterprise customers.",
        },
        actor="NovaCodePro",
    )
    service.submit_idea(project["id"], {"title": "Support portal", "problem": "Support workflows are manual."}, actor="customer-owner")
    service.run_discovery(project["id"], {"discovery_summary": "done"}, actor="business-analyst")
    service.create_requirement(project["id"], {"summary": "Support tickets must be traceable."}, actor="business-analyst")
    service.approve_requirements(project["id"], actor="product-manager")
    blueprint = service.generate_blueprint(project["id"], {"executive_summary": "Support portal blueprint"}, actor="architect")
    assert blueprint["provenance"]["generator"] == "NovaCodePro Solution Engine"
    service.create_architecture_decision(project["id"], {"decision": "Use NovaWorkflow Fabric"}, actor="architect")
    reopened = _service(db_path)
    replay = reopened.replay(project["id"])
    assert replay["timeline"]
    assert any(entry["action"] == "project.created" for entry in replay["timeline"])
    assert reopened.project(project["id"])["blueprint"]["provenance"]["generator"] == "NovaCodePro Solution Engine"

