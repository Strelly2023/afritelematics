from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import (
    build_afriprogramming_control_router,
)
from afritech.afriprogramming.persistence import PlatformStore


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afriprogramming_control_router())
    return TestClient(app)


def auth_headers(
    role: str = "DEVELOPER",
    user_id: str = "dev-1",
    organization_id: str = "org-nova",
) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_catalog_and_status_expose_control_plane_stack() -> None:
    client = build_client()

    status = client.get("/v1/novaprogramming/status")
    assert status.status_code == 200
    assert status.json()["status"] == "ready"

    catalog = client.get(
        "/v1/novaprogramming/catalog",
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["platform"] == "NovaProgramming"
    assert body["products"][0]["name"] == "NovaProgramming Studio"
    assert body["stack"]["frameworks"] == ["Django", "FastAPI", "Spring"]

    dashboard = client.get(
        "/v1/novaprogramming/dashboard?role=developers&project_id=project-employee-rbac",
        headers=auth_headers(role="DEVELOPER", user_id="dev-2"),
    )
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["view"] == "novaprogramming_dashboard"
    assert dashboard_body["status"]["platform"] == "NovaProgramming"
    assert dashboard_body["metrics"]["view"] == "novaprogramming_metrics"
    assert dashboard_body["staff_dashboard"]["role"] == "developers"


def test_studio_generation_and_intelligence_views_are_proposal_only() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novaprogramming/studio/generate-code",
        json={
            "prompt": "Build governed backend tools for staff operations",
            "mode": "code",
            "project_id": "project-employee-rbac",
        },
        headers=auth_headers(),
    )
    assert generated.status_code == 200
    body = generated.json()
    assert body["view"] == "novaprogramming_studio"
    assert body["generated_files"]
    assert body["engineering_plan"]["task"]["intent"] == "Build governed backend tools for staff operations"
    assert body["execution_preview"]["sandboxed"] is True

    explanation = client.post(
        "/v1/novaprogramming/studio/explain-code",
        json={"code": "def hello():\n    return 'ok'", "context": "sample"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert explanation.status_code == 200
    assert explanation.json()["summary"]["line_count"] == 2

    analysis = client.post(
        "/v1/novaprogramming/intelligence/analyze",
        json={"project_id": "project-employee-rbac", "focus": "repo intelligence"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert analysis.status_code == 200
    analysis_body = analysis.json()
    assert analysis_body["project"]["project_id"] == "project-employee-rbac"
    assert analysis_body["tech_debt_score"] >= 0


def test_cloud_governance_and_verify_flow_records_audit_events() -> None:
    client = build_client()

    request = client.post(
        "/v1/novaprogramming/cloud/request-deploy",
        json={
            "service": "api",
            "environment": "staging",
            "image": "nova-programming:latest",
            "rationale": "Release governed backend",
        },
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    assert request.status_code == 200
    request_body = request.json()
    assert request_body["status"] == "pending"
    request_id = request_body["request"]["request_id"]

    approval = client.post(
        "/v1/novaprogramming/governance/approve",
        json={
            "request_id": request_id,
            "decision": "approved",
            "notes": "Approved by governance",
        },
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"

    deploy = client.post(
        "/v1/novaprogramming/cloud/deploy",
        json={"request_id": request_id},
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    assert deploy.status_code == 200
    assert deploy.json()["status"] == "queued"

    proof = client.post(
        "/v1/novaprogramming/verify/generate-proof",
        json={
            "execution_id": "execution-001",
            "project_id": "project-employee-rbac",
            "payload": {"status": "ok", "surface": "studio"},
        },
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert proof.status_code == 200
    assert proof.json()["proof_hash"]

    replay = client.get(
        "/v1/novaprogramming/verify/execution-001",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert replay.status_code == 200
    assert replay.json()["replayable"] is True

    dashboard = client.get(
        "/v1/novaprogramming/staff/developers/dashboard?project_id=project-employee-rbac",
        headers=auth_headers(role="DEVELOPER", user_id="dev-2"),
    )
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["role"] == "developers"
    assert dashboard_body["role_surface"]["name"] == "Developers"
    assert dashboard_body["workspace"]["read_only"] is True

    audit = client.get(
        "/v1/novaprogramming/governance/audit-log",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert audit.status_code == 200
    assert audit.json()["count"] >= 4

    insights = client.get(
        "/v1/novaprogramming/insights",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert insights.status_code == 200
    assert insights.json()["organization_id"] == "org-nova"
    assert insights.json()["deployments"] >= 1


def test_cloud_deploy_requires_approved_request() -> None:
    client = build_client()

    denied = client.post(
        "/v1/novaprogramming/cloud/deploy",
        json={"request_id": "missing-request"},
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    assert denied.status_code == 404


def test_invalid_studio_payload_is_rejected() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novaprogramming/studio/generate-code",
        json={"prompt": "okay"},
        headers=auth_headers(role="DEVELOPER", user_id="dev-1"),
    )
    assert generated.status_code == 200

    invalid = client.post(
        "/v1/novaprogramming/studio/generate-code",
        json={"prompt": ""},
        headers=auth_headers(role="DEVELOPER", user_id="dev-1"),
    )
    assert invalid.status_code == 422


def test_trust_assurance_certification_and_billing_flow() -> None:
    client = build_client()

    request = client.post(
        "/v1/novaprogramming/cloud/request-deploy",
        json={
            "service": "api",
            "environment": "production",
            "image": "nova-programming:latest",
            "rationale": "trusted release",
        },
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    request_id = request.json()["request"]["request_id"]

    approved = client.post(
        "/v1/novaprogramming/governance/approve",
        json={"request_id": request_id, "decision": "approved", "notes": "go"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert approved.status_code == 200

    deployed = client.post(
        "/v1/novaprogramming/cloud/deploy",
        json={"request_id": request_id},
        headers=auth_headers(role="OPERATOR", user_id="operator-1"),
    )
    assert deployed.status_code == 200
    deployment_id = deployed.json()["deployment"]["deployment_id"]

    trust = client.get(
        "/v1/novaprogramming/trust",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert trust.status_code == 200
    trust_body = trust.json()
    assert "trust_score" in trust_body
    assert "classification" in trust_body

    assurance = client.get(
        f"/v1/novaprogramming/assurance/{deployment_id}",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert assurance.status_code == 200
    assurance_body = assurance.json()
    assert assurance_body["assurance_status"] in {"verified", "review"}
    assert assurance_body["receipt"]["receipt_hash"]

    replay = client.get(
        f"/v1/novaprogramming/trust/replay/{deployment_id}",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert replay.status_code == 200
    assert replay.json()["replay"]["replay_hash"]

    external = client.post(
        "/v1/novaprogramming/trust/verify-external",
        json={
            "organization_id": "org-nova",
            "proof_hash": assurance_body["proof_hash"],
            "audit_hash": assurance_body["audit_hash"],
            "receipt_hash": assurance_body["receipt"]["receipt_hash"],
        },
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert external.status_code == 200
    assert external.json()["result"]["valid"] is True

    certification = client.get(
        "/v1/novaprogramming/certification",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert certification.status_code == 200
    certification_body = certification.json()
    assert certification_body["certification_type"] == "CONTROLLED_OPERATIONAL_STATE"
    assert certification_body["classification"] == "CONTROLLED_OPERATIONAL_STATE"

    billing = client.get(
        "/v1/novaprogramming/billing/summary",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert billing.status_code == 200
    assert billing.json()["usage_total"] >= 1


def test_audit_chain_verification_detects_tampering(tmp_path: Path) -> None:
    store = PlatformStore(db_path=tmp_path / "store.sqlite3")
    store.record_audit_event(
        organization_id="org-chain",
        event_type="cloud.deploy",
        actor_user_id="user-1",
        actor_role="OPERATOR",
        target="api",
        status="queued",
        payload={"request_id": "req-1"},
    )
    store.record_audit_event(
        organization_id="org-chain",
        event_type="verify.generate_proof",
        actor_user_id="user-1",
        actor_role="VERIFIER",
        target="execution-1",
        status="recorded",
        payload={"proof_hash": "abc123"},
    )
    assert store.verify_audit_chain(organization_id="org-chain") is True

    with sqlite3.connect(store.db_path) as conn:
        chain_id = conn.execute(
            "SELECT chain_id FROM audit_chain_events WHERE organization_id = ? ORDER BY created_at ASC LIMIT 1",
            ("org-chain",),
        ).fetchone()[0]
        conn.execute(
            "UPDATE audit_chain_events SET previous_hash = ? WHERE chain_id = ?",
            ("tampered", chain_id),
        )
        conn.commit()

    assert store.verify_audit_chain(organization_id="org-chain") is False
