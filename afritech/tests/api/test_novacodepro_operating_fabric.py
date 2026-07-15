from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository
from afritech.novacodepro.operating_fabric import (
    MissingTrustedExecutionContext,
    canonical_event_contract,
    canonical_evidence_object,
    enterprise_object_envelope,
    normalize_role,
)


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _headers(role: str = "DEVELOPER", user_id: str = "usr_djuma") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_operating_fabric_contract_helpers_are_canonical() -> None:
    assert normalize_role("ADMIN") == "PLATFORM_ADMIN"
    assert normalize_role("SUPER_ADMIN") == "PLATFORM_OWNER"
    assert normalize_role("SYSTEM_ADMIN") == "PLATFORM_ADMIN"

    envelope = enterprise_object_envelope(object_id="obj-1", object_type="Capability", tenant_id="novatech")
    assert envelope["id"] == "obj-1"
    assert envelope["organization_id"] == "novatech"
    assert envelope["classification"] == "INTERNAL"

    event = canonical_event_contract(
        event_type="workflow.execution.completed",
        tenant_id="novatech",
        actor_type="AI_AGENT",
        actor_id="agent-release-validator",
        subject_type="DEPLOYMENT",
        subject_id="deployment-2026-101",
    )
    assert event["schema_version"] == "1.0"
    assert event["actor"]["type"] == "AI_AGENT"
    assert event["subject"]["id"] == "deployment-2026-101"

    evidence = canonical_evidence_object(
        evidence_type="RECOVERY_VALIDATION",
        subject_type="SERVICE_TWIN",
        subject_id="twin-payment-api-au",
        actor_id="recovery-agent",
        authority_reference="authority-recovery-l3",
        policy_results=["POL-RECOVERY-001:PASS"],
    )
    assert evidence["content_hash"].startswith("sha256:")
    assert evidence["verification_status"] == "VERIFIED"


def test_operating_fabric_requires_explicit_execution_context(tmp_path: Path) -> None:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    try:
        platform.submit_enterprise_request(
            {
                "title": "Payload authority must not bootstrap context",
                "request": "attempt direct call without trusted context",
                "tenant_id": "novatech",
                "roles": ["SUPER_ADMIN"],
                "runtime_environment": "test",
            }
        )
    except MissingTrustedExecutionContext as exc:
        assert "Payload-derived authority is prohibited" in str(exc)
    else:
        raise AssertionError("expected MissingTrustedExecutionContext")


def test_operating_fabric_manifest_and_role_endpoint(tmp_path: Path) -> None:
    client = _client(tmp_path)

    manifest_response = client.get("/v1/novacodepro/operating-fabric", headers=_headers("OBSERVER"))
    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["name"] == "NovaCodePro Unified Enterprise Operating Fabric"
    assert manifest["lifecycle"] == [
        "Describe",
        "Understand",
        "Model",
        "Plan",
        "Simulate",
        "Assess",
        "Approve",
        "Execute",
        "Observe",
        "Validate",
        "Record",
        "Learn",
        "Optimize",
    ]
    assert "Evidence and Assurance Fabric" in manifest["fabrics"]

    role_response = client.get("/v1/novacodepro/identity/roles/SUPER_ADMIN/normalize", headers=_headers("OBSERVER"))
    assert role_response.status_code == 200
    assert role_response.json()["canonical_role"] == "PLATFORM_OWNER"


def test_enterprise_request_operates_across_workflow_agents_twins_evidence_and_knowledge(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = {**_headers("DEVELOPER"), "Idempotency-Key": "idem-payment-recovery-001"}

    response = client.post(
        "/v1/novacodepro/enterprise-requests",
        headers=headers,
        json={
            "title": "Recover NovaPay payment API latency",
            "request": "Observe payment API latency, assess NovaPay impact, recommend recovery, validate business payment flow, and preserve evidence.",
            "capability_hint": "Payment Authorization Resilience",
            "capability_id": "cap-payment-authorization-resilience",
            "criticality": "TIER_0",
            "products": ["NovaPay"],
            "services": ["Payment API", "Ledger API"],
            "agents": ["sre-agent", "recovery-agent", "evidence-agent"],
            "dependencies": ["Primary Ledger", "NovaID"],
            "desired_outcomes": ["business payment validation", "signed evidence"],
            "requested_environment": "production",
            "rollback_expectation": "shift traffic back to primary after validation",
            "twin_id": "twin-payment-authorization-resilience",
            "tenant_id": "novatech",
            "roles": ["SUPER_ADMIN"],
            "authority_level": 5,
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["request_id"].startswith("enterprise-request-")
    assert body["workflow_id"].startswith("workflow-")
    assert body["status"] == "REVIEW_REQUIRED"
    assert body["status_url"] == f"/v1/novacodepro/workflows/{body['workflow_id']}"
    assert body["policy_outcome"] == "REQUIRE_APPROVAL"

    duplicate = client.post(
        "/v1/novacodepro/enterprise-requests",
        headers=headers,
        json={
            "title": "Recover NovaPay payment API latency",
            "request": "same command should return original result",
            "workspace_id": "workspace-platform",
            "capability_hint": "Payment Authorization Resilience",
        },
    )
    assert duplicate.status_code == 202
    assert duplicate.json()["workflow_id"] == body["workflow_id"]

    request_response = client.get(f"/v1/novacodepro/enterprise-requests/{body['request_id']}", headers=_headers("OBSERVER"))
    assert request_response.status_code == 200
    request_object = request_response.json()
    assert request_object["type"] == "Request"
    assert request_object["tenant_id"] == "novatech"
    assert request_object["owner_id"] == "usr_djuma"
    assert request_object["lifecycle_status"] == "REVIEW_REQUIRED"
    assert request_object["data"]["canonical_roles"] == ["DEVELOPER"]
    assert "roles" not in request_object["data"]["requested_metadata"]

    objects_response = client.get("/v1/novacodepro/enterprise-objects", headers=_headers("OBSERVER"))
    assert objects_response.status_code == 200
    assert any(item["id"] == "cap-payment-authorization-resilience" for item in objects_response.json())

    capabilities_response = client.get("/v1/novacodepro/enterprise-capabilities", headers=_headers("OBSERVER"))
    assert capabilities_response.status_code == 200
    assert any(item["id"] == "cap-payment-authorization-resilience" for item in capabilities_response.json())

    command_response = client.get("/v1/novacodepro/command-center", headers=_headers("OBSERVER"))
    assert command_response.status_code == 200
    assert command_response.json()["status"] == "READY"

    workflow_response = client.get(f"/v1/novacodepro/workflows/{body['workflow_id']}", headers=_headers("OBSERVER"))
    assert workflow_response.status_code == 200
    workflow = workflow_response.json()
    assert workflow["status"] == "planning"
    assert workflow["durability"]["material_execution_blocked"] is True

    agent_response = client.get("/v1/novacodepro/agents/executions", headers=_headers("OBSERVER"))
    assert agent_response.status_code == 200
    assert [item for item in agent_response.json() if item.get("workflow_id") == body["workflow_id"]] == []

    events_response = client.get("/v1/novacodepro/events", headers=_headers("OBSERVER"))
    assert events_response.status_code == 200
    event_types = {item["event_type"] for item in events_response.json()}
    assert "enterprise.request.accepted" in event_types
    assert "digital_twin.observed" in event_types

    relationships_response = client.get("/v1/novacodepro/enterprise-relationships", headers=_headers("OBSERVER"))
    assert relationships_response.status_code == 200
    relationships = relationships_response.json()
    assert {item["relationship_type"] for item in relationships} >= {"DEPENDS_ON", "REPRESENTS", "EVIDENCED_BY"}
    assert all(item["assertion_type"] in {"DECLARED", "OBSERVED", "APPROVED"} for item in relationships)

    evidence_response = client.get("/v1/novacodepro/evidence/bundles", headers=_headers("OBSERVER"))
    assert evidence_response.status_code == 200
    evidence = next(item for item in evidence_response.json() if item.get("workflow_id") == body["workflow_id"])
    verify_response = client.post(f"/v1/novacodepro/evidence/bundles/{evidence['id']}/verify", headers=_headers("OBSERVER"))
    assert verify_response.status_code == 200
    assert verify_response.json()["verified"] is True
    assert verify_response.json()["verification_status"] == "DEVELOPMENT_VERIFIED"

    knowledge_response = client.get("/v1/novacodepro/knowledge/nodes", headers=_headers("OBSERVER"))
    assert knowledge_response.status_code == 200
    knowledge = next(item for item in knowledge_response.json() if item["id"] == f"knw-{body['workflow_id']}")
    assert knowledge["lifecycle_status"] == "DRAFT"
    assert knowledge["memory_promotion"] == "BLOCKED_PENDING_REVIEW"


def test_enterprise_request_rejects_payload_authority_and_requires_idempotency(tmp_path: Path) -> None:
    client = _client(tmp_path)

    missing_idempotency = client.post(
        "/v1/novacodepro/enterprise-requests",
        headers=_headers("DEVELOPER"),
        json={"title": "No idempotency", "request": "missing key"},
    )
    assert missing_idempotency.status_code == 400

    tenant_switch = client.post(
        "/v1/novacodepro/enterprise-requests",
        headers={**_headers("DEVELOPER"), "Idempotency-Key": "idem-tenant-switch"},
        json={
            "title": "Attempt tenant switch",
            "request": "payload tries to switch tenant",
            "tenant_id": "other-tenant",
            "roles": ["SUPER_ADMIN"],
            "authority_level": 5,
        },
    )
    assert tenant_switch.status_code == 403
    assert tenant_switch.json()["detail"] == "requested_tenant_mismatch"


def test_approval_self_approval_is_blocked_and_maturity_is_honest(tmp_path: Path) -> None:
    client = _client(tmp_path)
    create = client.post(
        "/v1/novacodepro/enterprise-requests",
        headers={**_headers("DEVELOPER", "usr_requester"), "Idempotency-Key": "idem-self-approval"},
        json={
            "title": "Approval integrity request",
            "request": "create approval and block self approval",
            "requested_environment": "production",
            "capability_hint": "Release Governance",
            "criticality": "TIER_0",
        },
    )
    assert create.status_code == 202
    approval_id = create.json()["approval_id"]

    self_approval = client.post(
        f"/v1/novacodepro/approvals/{approval_id}/approve",
        headers=_headers("DEVELOPER", "usr_requester"),
        json={"note": "self approval should fail"},
    )
    assert self_approval.status_code == 403
    assert self_approval.json()["detail"] == "segregation_of_duties_violation"

    valid_approval = client.post(
        f"/v1/novacodepro/approvals/{approval_id}/approve",
        headers=_headers("ADMIN", "usr_approver"),
        json={"note": "independent approval"},
    )
    assert valid_approval.status_code == 200
    assert valid_approval.json()["status"] in {"PARTIALLY_APPROVED", "APPROVED"}
    assert valid_approval.json()["votes"][0]["subject_id"] == "usr_approver"

    maturity = client.get("/v1/novacodepro/operating-fabric/maturity", headers=_headers("OBSERVER"))
    assert maturity.status_code == 200
    report = maturity.json()
    assert report["status"] == "ADVANCED_IMPLEMENTATION_IN_PROGRESS"
    assert report["score"] < 10
    assert any("AWS KMS" in " ".join(domain["exceptions"]) for domain in report["domains"])
