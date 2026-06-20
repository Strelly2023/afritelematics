from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import build_afriprogramming_control_router
from afritech.afriprogramming.assurance import (
    DistributedTrustNetworkService,
    EventStreamingService,
    PKIService,
    SignedAuditChainService,
    WorkflowService,
    ZeroTrustService,
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
    return PlatformStore(db_path=tmp_path / "novaprogramming-v7.sqlite3")


def test_key_rotation_updates_pki_and_signed_audit_chain(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"

    store.record_audit_event(
        organization_id=org_id,
        event_type="bootstrap",
        actor_user_id="system",
        actor_role="operator",
        target="core",
        status="recorded",
        payload={"step": 1},
    )
    pki = PKIService(store)
    current = pki.current_key(organization_id=org_id)
    rotated = pki.rotate(organization_id=org_id, rotated_by="rotator", reason="scheduled")
    store.record_audit_event(
        organization_id=org_id,
        event_type="deploy",
        actor_user_id="system",
        actor_role="operator",
        target="api",
        status="approved",
        payload={"step": 2},
    )

    assert current["key_version"] == 1
    assert rotated["key_version"] == 2
    assert store.verify_signed_audit_chain(organization_id=org_id) is True
    assert store.list_key_rotations(organization_id=org_id)
    assert store.list_signing_keys(organization_id=org_id, key_family="audit")[0]["status"] == "active"


def test_distributed_trust_network_and_federation_claims(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = DistributedTrustNetworkService(store)

    node = service.register_peer(
        organization_id=org_id,
        peer_organization_id="peer-org",
        jurisdiction="commercial",
        role="verifier",
        public_key_id="peer-key-1",
        endpoint="https://peer.example/api",
    )
    claim = service.issue_claim(
        organization_id=org_id,
        peer_organization_id="peer-org",
        claim_type="receipt",
        payload={
            "proof_hash": "p" * 64,
            "audit_hash": "a" * 64,
            "receipt_hash": "r" * 64,
            "certification_hash": "c" * 64,
        },
    )

    verification = service.verify_claim(claim)
    certificate = service.federation_certificate(quorum=2)

    assert node["peer_organization_id"] == "peer-org"
    assert verification["valid"] is True
    assert certificate["verification"]["verified"] is True
    assert service.events(org_id)
    assert service.claims(org_id)


def test_event_streaming_publish_and_consume(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = EventStreamingService(store)

    service.create_topic(
        organization_id=org_id,
        topic_name="deployment-events",
        description="deployment lifecycle",
        retention_days=30,
    )
    published = service.publish(
        organization_id=org_id,
        topic_name="deployment-events",
        event_type="deployment.started",
        payload={"deployment_id": "dep-1"},
        partition_key="dep-1",
    )
    consumed = service.consume(organization_id=org_id, topic_name="deployment-events")

    assert published["offset_number"] == 1
    assert consumed and consumed[0]["event_type"] == "deployment.started"
    assert service.topics(org_id)[0]["topic_name"] == "deployment-events"


def test_temporal_style_workflow_lifecycle(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = WorkflowService(store)

    workflow = service.start(
        organization_id=org_id,
        workflow_name="deployment",
        input_payload={"service": "api"},
    )
    updated = service.signal(
        organization_id=org_id,
        workflow_id=workflow["workflow_id"],
        signal_name="approved",
        payload={"approved": True},
    )

    assert workflow["state"] == "running"
    assert updated["state"] == "running"
    assert service.status(organization_id=org_id, workflow_id=workflow["workflow_id"])["workflow_id"] == workflow["workflow_id"]
    assert len(service.history(organization_id=org_id, workflow_id=workflow["workflow_id"])) >= 2


def test_zero_trust_enforces_cross_org_and_certification_rules(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"
    service = ZeroTrustService(store)
    service.seed_defaults(org_id)

    denied = service.evaluate(
        organization_id=org_id,
        subject="developer-1",
        action="access",
        resource="peer-resource",
        context={"cross_org": True, "device_trust": "untrusted"},
    )
    allowed = service.evaluate(
        organization_id=org_id,
        subject="verifier-1",
        action="certification",
        resource="platform",
        context={"trust_score": 95, "signed_audit_valid": True},
    )

    assert denied["allowed"] is False
    assert allowed["allowed"] is True
    assert service.decisions(org_id)


def test_v7_api_surface_exposes_new_capabilities() -> None:
    client = build_client()
    org_id = f"org-{uuid4().hex[:8]}"
    headers = auth_headers("VERIFIER", "verifier-1", org_id)

    key_rotate = client.post(
        "/v1/novaprogramming/keys/rotate",
        json={"reason": "scheduled"},
        headers=headers,
    )
    assert key_rotate.status_code == 200

    stream_topic = client.post(
        "/v1/novaprogramming/stream/topics/create",
        json={"topic_name": "audit-stream", "description": "audit events", "retention_days": 14},
        headers=headers,
    )
    assert stream_topic.status_code == 200

    workflow = client.post(
        "/v1/novaprogramming/workflows/start",
        json={"workflow_name": "deployment", "input_payload": {"service": "api"}},
        headers=headers,
    )
    assert workflow.status_code == 200
    workflow_id = workflow.json()["workflow"]["workflow_id"]

    signed = client.get("/v1/novaprogramming/audit/signed", headers=headers)
    assert signed.status_code == 200

    status = client.get(
        f"/v1/novaprogramming/workflows/{workflow_id}",
        headers=headers,
    )
    assert status.status_code == 200
    assert status.json()["workflow_id"] == workflow_id

    zero_trust = client.post(
        "/v1/novaprogramming/zero-trust/evaluate",
        json={
            "subject": "developer-1",
            "action": "access",
            "resource": "peer-resource",
            "context": {"cross_org": True},
        },
        headers=headers,
    )
    assert zero_trust.status_code == 200
    assert zero_trust.json()["allowed"] is False
