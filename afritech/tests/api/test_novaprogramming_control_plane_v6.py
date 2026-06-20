from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import build_afriprogramming_control_router
from afritech.afriprogramming.assurance import (
    CertificationService,
    ContinuousAssuranceService,
    PolicyRegistryService,
    RetentionService,
    TrustExchangeService,
    TrustTrendService,
    verify_signed_certification,
)
from afritech.afriprogramming.persistence import PlatformStore


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afriprogramming_control_router())
    return TestClient(app)


def auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def build_store(tmp_path: Path) -> PlatformStore:
    return PlatformStore(db_path=tmp_path / "novaprogramming-v6.sqlite3")


def test_policy_registry_creates_versions_and_records_decisions(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    registry = PolicyRegistryService(store)
    org_id = f"org-{uuid4().hex[:8]}"

    created_v1 = registry.create_policy(
        organization_id=org_id,
        policy_name="deployment_requires_approval",
        version="v1",
        rule_type="deployment",
        rule_payload={"require_approval": True},
        active=True,
        created_by="tester",
    )
    created_v2 = registry.create_policy(
        organization_id=org_id,
        policy_name="deployment_requires_approval",
        version="v2",
        rule_type="deployment",
        rule_payload={"require_approval": True, "requires_verifier": True},
        active=True,
        created_by="tester",
    )

    policies = registry.list_policies(org_id)
    assert {created_v1["version"], created_v2["version"]} == {"v1", "v2"}
    assert len([policy for policy in policies if policy["policy_name"] == "deployment_requires_approval"]) == 2

    decision = registry.evaluate(
        organization_id=org_id,
        action="deploy",
        actor_user_id="operator-1",
        target="api",
        payload={"approved": False, "environment": "production", "actor_role": "OPERATOR"},
    )
    assert decision["allowed"] is False
    assert registry.decisions(org_id)[0]["decision_id"] == decision["decision_id"]


def test_certification_issue_and_verify_round_trip(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    store.store_trust_score(
        organization_id=org_id,
        trust_score=94,
        classification="HIGH_TRUST",
        breakdown={"policy_compliance": 100},
        findings=["system operating at high trust"],
    )
    store.store_assurance_record(
        organization_id=org_id,
        deployment_id="deploy-1",
        trust_score=94,
        risk_score=6,
        proof_coverage=98,
        policy_compliance=100,
        assurance_status="verified",
        payload={"assurance_status": "verified"},
    )

    service = CertificationService(store)
    issued = service.issue(organization_id=org_id)
    verification = service.verify(issued)

    assert issued["certification_hash"]
    assert issued["signature"]
    assert issued["public_key_id"]
    assert verification["valid"] is True
    assert verify_signed_certification(issued)["valid"] is True


def test_invalid_certification_fails(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    store.store_trust_score(
        organization_id=org_id,
        trust_score=90,
        classification="HIGH_TRUST",
        breakdown={},
        findings=[],
    )
    service = CertificationService(store)
    issued = service.issue(organization_id=org_id)
    tampered = {**issued, "certification_hash": "0" * 64}
    assert service.verify(tampered)["valid"] is False


def test_assurance_run_creates_history_and_alerts(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    assurance = ContinuousAssuranceService(store)

    run = assurance.run(organization_id=org_id, actor_user_id="assurance-bot")
    history = assurance.history(organization_id=org_id)
    alerts = assurance.alerts(organization_id=org_id)

    assert run["organization_id"] == org_id
    assert history and history[0]["assurance_run_id"] == run["assurance_run_id"]
    assert isinstance(alerts, list)


def test_trust_trends_improve_and_degrade(tmp_path: Path) -> None:
    improving_store = build_store(tmp_path / "improving")
    org_improving = f"org-{uuid4().hex[:8]}"
    improving_store.store_trust_score(
        organization_id=org_improving,
        trust_score=60,
        classification="LOW_TRUST",
        breakdown={},
        findings=[],
    )
    improving_store.store_trust_score(
        organization_id=org_improving,
        trust_score=62,
        classification="MEDIUM_TRUST",
        breakdown={},
        findings=[],
    )
    improving_store.store_trust_score(
        organization_id=org_improving,
        trust_score=64,
        classification="HIGH_TRUST",
        breakdown={},
        findings=[],
    )
    improving = TrustTrendService(improving_store).compute(org_improving)
    assert improving["direction"] == "improving"

    degrading_store = build_store(tmp_path / "degrading")
    org_degrading = f"org-{uuid4().hex[:8]}"
    degrading_store.store_trust_score(
        organization_id=org_degrading,
        trust_score=64,
        classification="HIGH_TRUST",
        breakdown={},
        findings=[],
    )
    degrading_store.store_trust_score(
        organization_id=org_degrading,
        trust_score=62,
        classification="MEDIUM_TRUST",
        breakdown={},
        findings=[],
    )
    degrading_store.store_trust_score(
        organization_id=org_degrading,
        trust_score=60,
        classification="LOW_TRUST",
        breakdown={},
        findings=[],
    )
    degrading = TrustTrendService(degrading_store).compute(org_degrading)
    assert degrading["direction"] == "degrading"


def test_retention_defaults_block_deletion(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    retention = RetentionService(store)

    check = retention.check(org_id)
    assert check["records"]["audit"]["deletion_allowed"] is False
    assert check["records"]["proof"]["deletion_allowed"] is False
    assert check["records"]["certification"]["deletion_allowed"] is False


def test_assurance_report_is_generated(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    store.store_trust_score(
        organization_id=org_id,
        trust_score=91,
        classification="HIGH_TRUST",
        breakdown={},
        findings=["healthy"],
    )
    store.store_assurance_record(
        organization_id=org_id,
        deployment_id="deploy-1",
        trust_score=91,
        risk_score=9,
        proof_coverage=97,
        policy_compliance=100,
        assurance_status="verified",
        payload={"assurance_status": "verified"},
    )
    store.store_policy_definition(
        organization_id=org_id,
        policy_name="deployment_requires_approval",
        version="v1",
        rule_type="deployment",
        rule_payload={"require_approval": True},
        active=True,
        created_by="tester",
    )
    report = store.list_assurance_reports(organization_id=org_id)
    assert report == []
    from afritech.afriprogramming.assurance import AssuranceReportService

    generated = AssuranceReportService(store).build(
        organization_id=org_id,
        report_classification="CLIENT_ASSURANCE_REPORT",
    )
    latest = AssuranceReportService(store).latest(org_id)
    assert generated["report_classification"] == "CLIENT_ASSURANCE_REPORT"
    assert latest is not None
    assert latest["report_classification"] == "CLIENT_ASSURANCE_REPORT"


def test_trust_exchange_verifies_public_receipt(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    store.store_trust_score(
        organization_id=org_id,
        trust_score=93,
        classification="HIGH_TRUST",
        breakdown={},
        findings=[],
    )
    store.store_assurance_record(
        organization_id=org_id,
        deployment_id="deploy-1",
        trust_score=93,
        risk_score=7,
        proof_coverage=99,
        policy_compliance=100,
        assurance_status="verified",
        payload={"assurance_status": "verified"},
    )
    cert = CertificationService(store).issue(organization_id=org_id)
    receipt = {
        "organization_id": org_id,
        "proof_hash": "p" * 64,
        "audit_hash": "a" * 64,
        "receipt_hash": "r" * 64,
        "certification_hash": cert["certification_hash"],
        "signature": cert["signature"],
        "public_key_id": cert["public_key_id"],
        "payload": cert["payload"],
    }
    result = TrustExchangeService(store).verify_public_receipt(
        organization_id=org_id,
        receipt=receipt,
    )
    assert result["valid"] is True
    assert store.list_trust_exchange_events(organization_id=org_id)


def test_trust_exchange_rejects_malformed_receipt(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    result = TrustExchangeService(store).verify_public_receipt(
        organization_id="org-test",
        receipt={"organization_id": "org-test", "proof_hash": "short"},
    )
    assert result["valid"] is False


def test_v6_api_surface_enforces_roles_and_routes() -> None:
    client = build_client()
    organization_id = f"org-{uuid4().hex[:8]}"

    observer_policy = client.post(
        "/v1/novaprogramming/policies",
        json={
            "policy_name": "deployment_requires_approval",
            "version": "v1",
            "rule_type": "deployment",
            "rule_payload": {"require_approval": True},
        },
        headers=auth_headers("OBSERVER", "observer-1", organization_id),
    )
    assert observer_policy.status_code == 403

    operator_cert = client.post(
        "/v1/novaprogramming/certification/issue",
        json={"certification_type": "CONTROLLED_OPERATIONAL_STATE"},
        headers=auth_headers("OPERATOR", "operator-1", organization_id),
    )
    assert operator_cert.status_code == 403

    developer_cert = client.post(
        "/v1/novaprogramming/certification/issue",
        json={"certification_type": "CONTROLLED_OPERATIONAL_STATE"},
        headers=auth_headers("DEVELOPER", "dev-1", organization_id),
    )
    assert developer_cert.status_code == 403

    verifier_policy = client.post(
        "/v1/novaprogramming/policies",
        json={
            "policy_name": "deployment_requires_approval",
            "version": "v1",
            "rule_type": "deployment",
            "rule_payload": {"require_approval": True},
        },
        headers=auth_headers("VERIFIER", "verifier-1", organization_id),
    )
    assert verifier_policy.status_code == 200


def test_deployment_is_blocked_without_approval() -> None:
    client = build_client()
    organization_id = f"org-{uuid4().hex[:8]}"

    request = client.post(
        "/v1/novaprogramming/cloud/request-deploy",
        json={
            "service": "api",
            "environment": "production",
            "image": "nova-programming:latest",
            "rationale": "test blocked deploy",
        },
        headers=auth_headers("OPERATOR", "operator-1", organization_id),
    )
    assert request.status_code == 200
    request_id = request.json()["request"]["request_id"]

    deploy = client.post(
        "/v1/novaprogramming/cloud/deploy",
        json={"request_id": request_id},
        headers=auth_headers("OPERATOR", "operator-1", organization_id),
    )
    assert deploy.status_code == 403


def test_assurance_trend_and_report_routes_return_structured_data() -> None:
    client = build_client()
    organization_id = f"org-{uuid4().hex[:8]}"

    run = client.post(
        "/v1/novaprogramming/assurance/run",
        json={"actor_user_id": "assurance-bot"},
        headers=auth_headers("VERIFIER", "verifier-2", organization_id),
    )
    assert run.status_code == 200

    status = client.get(
        "/v1/novaprogramming/assurance/status",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert status.status_code == 200
    assert status.json()["organization_id"] == organization_id

    history = client.get(
        "/v1/novaprogramming/assurance/history",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert history.status_code == 200
    assert history.json()["runs"]

    alerts = client.get(
        "/v1/novaprogramming/assurance/alerts",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert alerts.status_code == 200

    trends = client.get(
        "/v1/novaprogramming/trust/trends",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert trends.status_code == 200
    assert "current_score" in trends.json()

    retention = client.get(
        "/v1/novaprogramming/retention/check",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert retention.status_code == 200
    assert retention.json()["records"]["audit"]["deletion_allowed"] is False

    report = client.get(
        "/v1/novaprogramming/reports/assurance",
        headers=auth_headers("OBSERVER", "observer-2", organization_id),
    )
    assert report.status_code == 200
    assert report.json()["report"]["report_classification"] == "INTERNAL_ASSURANCE_REPORT"
