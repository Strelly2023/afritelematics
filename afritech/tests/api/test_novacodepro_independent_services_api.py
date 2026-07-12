from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(service))
    return TestClient(app)


def _headers(role: str = "OPERATOR", user_id: str = "platform-admin") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_novacodepro_independent_cloud_services_contract(tmp_path: Path) -> None:
    client = _client(tmp_path)

    agent = client.get("/v1/novacodepro/agents", headers=_headers())
    assert agent.status_code == 200
    assert any(item["id"] == "architecture-agent" for item in agent.json())

    risk = client.post(
        "/v1/novacodepro/risks/evaluate",
        headers=_headers(role="DEVELOPER"),
        json={
            "title": "Production payment-service release",
            "likelihood": "medium",
            "impact": "high",
            "exposure": "high",
            "required_controls": ["security_approval", "rollback_plan"],
        },
    )
    assert risk.status_code == 200
    risk_id = risk.json()["id"]
    assert risk.json()["classification"] in {"HIGH", "CRITICAL"}

    policy = client.post(
        "/v1/novacodepro/policies/evaluate",
        headers=_headers(role="DEVELOPER"),
        json={
            "policy_id": "REL-PROD-001",
            "environment": "production",
            "approvals": ["RELEASE"],
        },
    )
    assert policy.status_code == 200
    assert policy.json()["decision"] == "DENY"
    assert "security_approval_missing" in policy.json()["reasons"]

    evidence = client.post(
        "/v1/novacodepro/evidence/bundles",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": "workflow-ride-platform",
            "action": "release.approved",
            "policy_id": "REL-PROD-001",
            "artifact_ids": ["artifact-1", "artifact-2"],
            "payload": {"release_id": "release-ride-platform"},
        },
    )
    assert evidence.status_code == 200
    evidence_id = evidence.json()["id"]

    verified = client.post(
        f"/v1/novacodepro/evidence/bundles/{evidence_id}/verify",
        headers=_headers(),
    )
    assert verified.status_code == 200
    assert verified.json()["verified"] is True

    node = client.post(
        "/v1/novacodepro/knowledge/nodes",
        headers=_headers(role="DEVELOPER"),
        json={"id": "req-42", "label": "Requirement RQ-42", "type": "requirement", "links": ["arch-18"]},
    )
    assert node.status_code == 200

    relationship = client.post(
        "/v1/novacodepro/knowledge/relationships",
        headers=_headers(role="DEVELOPER"),
        json={"source_id": "req-42", "target_id": "kg-release"},
    )
    assert relationship.status_code == 200

    trace = client.get("/v1/novacodepro/knowledge/trace/req-42", headers=_headers())
    assert trace.status_code == 200
    assert trace.json()["node"]["id"] == "req-42"

    graph = client.post(
        "/v1/novacodepro/graph/query",
        headers=_headers(role="DEVELOPER"),
        json={"query": "Requirement"},
    )
    assert graph.status_code == 200
    assert graph.json()["count"] >= 1

    federation = client.post(
        "/v1/novacodepro/federation/agreements",
        headers=_headers(role="ADMIN"),
        json={
            "consumer_org": "partner-bank",
            "allowed_capabilities": ["knowledge.read", "evidence.verify"],
            "allowed_regions": ["AU"],
            "purpose": "Partner integration",
        },
    )
    assert federation.status_code == 200
    federation_id = federation.json()["id"]

    authorized = client.post(
        "/v1/novacodepro/federation/authorize",
        headers=_headers(role="OBSERVER"),
        json={"capability": "knowledge.read", "region": "AU"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["decision"] == "ALLOW"

    twin = client.post(
        "/v1/novacodepro/twins/twin-novacodepro/simulate",
        headers=_headers(role="DEVELOPER"),
        json={"scenario": "REGION_FAILURE"},
    )
    assert twin.status_code == 200
    assert twin.json()["approval_required"] is True

    council = client.post(
        "/v1/novacodepro/executive/council/sessions",
        headers=_headers(role="DEVELOPER"),
        json={"subject": "Expansion", "question": "What threatens Q3 objectives?"},
    )
    assert council.status_code == 200

    board = client.post(
        "/v1/novacodepro/board/meetings",
        headers=_headers(role="ADMIN"),
        json={"title": "Q3 Board", "agenda": ["Expansion"]},
    )
    assert board.status_code == 200

    sli = client.post(
        "/v1/novacodepro/sre/slis",
        headers=_headers(role="ADMIN"),
        json={"service": "novacodepro-gateway", "metric": "availability"},
    )
    assert sli.status_code == 200

    release = client.post(
        "/v1/novacodepro/releases",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": "workflow-ride-platform",
            "title": "Public pilot release",
            "channel": "pilot",
            "target": "staging",
            "notes": "contract test",
        },
    )
    assert release.status_code == 200
    release_id = release.json()["id"]

    signed = client.post(
        f"/v1/novacodepro/releases/{release_id}/sign",
        headers=_headers(role="DEVELOPER"),
        json={"signature": "sig-release"},
    )
    assert signed.status_code == 200
    assert signed.json()["status"] == "signed"

    deployment = client.post(
        "/v1/novacodepro/deployments",
        headers=_headers(role="DEVELOPER"),
        json={
            "workflow_id": "workflow-ride-platform",
            "release_id": release_id,
            "environment": "production",
            "region": "Australia",
            "version": "2027.1.0",
            "metrics": {"availability": 0.999, "latency_p95_ms": 100, "error_rate": 0.0001},
        },
    )
    assert deployment.status_code == 200
    deployment_id = deployment.json()["id"]

    blocked = client.post(
        f"/v1/novacodepro/deployments/{deployment_id}/start",
        headers=_headers(role="DEVELOPER"),
        json={"environment": "production"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "deployment_prerequisites_failed"

    package = client.post(
        "/v1/novacodepro/marketplace/packages",
        headers=_headers(role="ADMIN"),
        json={
            "package_id": "ride-hailing-agent",
            "version": "2027.1.0",
            "signature": "sigstore-reference",
            "checksum": "sha256-demo",
        },
    )
    assert package.status_code == 200

    installation = client.post(
        "/v1/novacodepro/marketplace/installations",
        headers=_headers(role="ADMIN"),
        json={
            "package_id": "ride-hailing-agent",
            "version": "2027.1.0",
            "signature": "sigstore-reference",
            "checksum": "sha256-demo",
        },
    )
    assert installation.status_code == 200
    assert installation.json()["installed"] is True

    ops = client.get("/v1/novacodepro/operations/health", headers=_headers())
    assert ops.status_code == 200
    assert ops.json()["incident_count"] >= 1

    command_center = client.get("/v1/novacodepro/executive/command-center", headers=_headers())
    assert command_center.status_code == 200
    assert command_center.json()["enterprise_health"] == 96
    assert command_center.json()["status"]["command_center_ready"] is True

    assert federation_id
    assert risk_id
