from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.afriprogramming_control_api import build_afriprogramming_control_router
from afritech.afriprogramming.persistence import PlatformStore
from afritech.afriprogramming.v9 import (
    AssuranceScheduler,
    CertificateTransparencyLogService,
    KeyRevocationAuthority,
    OpenTelemetryTracingService,
    TrustFabricConsensusService,
    build_v9_postgres_schema_sql,
    build_v9_rls_sql,
    ensure_v9_schema,
)


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_afriprogramming_control_router())
    return TestClient(app)


def auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def build_store(tmp_path: Path) -> PlatformStore:
    return PlatformStore(db_path=tmp_path / "novaprogramming-v9.sqlite3")


def test_v9_schema_sql_and_rls_are_composite_and_partitioned() -> None:
    schema_sql = build_v9_postgres_schema_sql(partition_count=8)
    rls_sql = build_v9_rls_sql()

    assert "PARTITION BY HASH (organization_id)" in schema_sql
    assert "PRIMARY KEY (organization_id, round_id)" in schema_sql
    assert "UNIQUE (organization_id, certificate_hash)" in schema_sql
    assert "ENABLE ROW LEVEL SECURITY" in rls_sql
    assert "current_setting('app.organization_id', true)" in rls_sql


def test_v9_schema_is_created_for_sqlite_store(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    bundle = ensure_v9_schema(store, partition_count=4)

    with store._connect() as conn:  # noqa: SLF001 - test boundary shim
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    tables = {str(row["name"]) for row in rows}
    assert {"trust_consensus_rounds", "certificate_transparency_log", "trace_spans"} <= tables
    assert bundle["schema_sql"]


def test_v9_services_cover_consensus_ct_revocation_trace_and_scheduler(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    org_id = f"org-{uuid4().hex[:8]}"

    consensus_service = TrustFabricConsensusService(store)
    consensus = consensus_service.evaluate(
        organization_id=org_id,
        proposal={"action": "deploy", "service": "api"},
        peer_votes=[
            {
                "peer_organization_id": "peer-a",
                "region_id": "melbourne",
                "vote": "accept",
                "weight": 0.95,
                "latency_ms": 65,
                "signature": "sig-a",
                "public_key_id": "key-a",
                "reason": "healthy peer",
            },
            {
                "peer_organization_id": "peer-b",
                "region_id": "singapore",
                "vote": "accept",
                "weight": 0.9,
                "latency_ms": 72,
                "signature": "sig-b",
                "public_key_id": "key-b",
                "reason": "healthy peer",
            },
        ],
        quorum=1,
    )
    assert consensus["decision"] == "accepted"
    assert consensus_service.latest_round(org_id)["consensus_hash"]

    ct_service = CertificateTransparencyLogService(store)
    entry = ct_service.append(
        organization_id=org_id,
        subject="nova.example",
        issuer="NovaProgramming PKI",
        key_family="audit",
    )
    assert ct_service.verify(org_id)["valid"] is True
    assert entry["chain_hash"]

    key_service = KeyRevocationAuthority(store)
    key_bundle = store.rotate_signing_key(
        organization_id=org_id,
        key_family="audit",
        rotated_by="operator",
        reason="rotation",
    )
    revocation = key_service.revoke(
        organization_id=org_id,
        key_id=key_bundle["key_id"],
        reason="compromised",
        revoked_by="operator",
    )
    assert revocation["status"] == "revoked"
    assert key_service.revocations(org_id)[0]["key_id"] == key_bundle["key_id"]

    tracing_service = OpenTelemetryTracingService(store)
    span = tracing_service.record_span(
        organization_id=org_id,
        actor_user_id="user-1",
        operation_name="POST /v1/novaprogramming/v9/traces",
        endpoint="/v1/novaprogramming/v9/traces",
        latency_ms=11,
        status_code=200,
        proof_hash="proof-1",
        deployment_id="deploy-1",
        attributes={"route": "v9"},
    )
    assert span["span_id"]
    assert tracing_service.spans(org_id)[0]["endpoint"] == "/v1/novaprogramming/v9/traces"

    scheduler = AssuranceScheduler(store)
    runs = scheduler.run_once([org_id])
    assert runs[0]["organization_id"] == org_id
    assert scheduler.history(org_id)[0]["scheduler_run_id"] == runs[0]["scheduler_run_id"]


def test_v9_fastapi_routes_expose_hardened_endpoints() -> None:
    client = build_client()
    org_id = f"org-{uuid4().hex[:8]}"
    headers = auth_headers("VERIFIER", "verifier-v9", org_id)

    schema = client.get("/v1/novaprogramming/v9/schema?partition_count=6", headers=headers)
    assert schema.status_code == 200
    assert schema.json()["platform_version"] == "V9"

    consensus = client.post(
        "/v1/novaprogramming/v9/trust/consensus",
        json={
            "proposal": {"action": "deploy", "service": "api"},
            "peer_votes": [
                {
                    "peer_organization_id": "peer-a",
                    "region_id": "melbourne",
                    "vote": "accept",
                    "weight": 0.95,
                    "latency_ms": 60,
                    "signature": "sig-a",
                    "public_key_id": "key-a",
                },
                {
                    "peer_organization_id": "peer-b",
                    "region_id": "singapore",
                    "vote": "accept",
                    "weight": 0.9,
                    "latency_ms": 70,
                    "signature": "sig-b",
                    "public_key_id": "key-b",
                },
            ],
            "quorum": 1,
        },
        headers=headers,
    )
    assert consensus.status_code == 200
    assert consensus.json()["decision"] == "accepted"

    ct_append = client.post(
        "/v1/novaprogramming/v9/certificate-transparency",
        json={"subject": "nova.example", "issuer": "NovaProgramming PKI"},
        headers=headers,
    )
    assert ct_append.status_code == 200
    assert client.get("/v1/novaprogramming/v9/certificate-transparency", headers=headers).status_code == 200

    rotate = client.post(
        "/v1/novaprogramming/keys/rotate",
        json={"key_family": "audit", "rotated_by": "operator", "reason": "rotation"},
        headers=headers,
    )
    assert rotate.status_code == 200
    key_id = rotate.json()["rotation"]["key_id"]

    revocation = client.post(
        "/v1/novaprogramming/v9/keys/revoke",
        json={"key_id": key_id, "reason": "compromised", "revoked_by": "operator"},
        headers=headers,
    )
    assert revocation.status_code == 200
    assert client.get("/v1/novaprogramming/v9/keys/revocations", headers=headers).status_code == 200

    trace = client.post(
        "/v1/novaprogramming/v9/traces",
        json={
            "actor_user_id": "user-1",
            "operation_name": "POST /v1/novaprogramming/v9/traces",
            "endpoint": "/v1/novaprogramming/v9/traces",
            "latency_ms": 11,
            "status_code": 200,
            "attributes": {"route": "v9"},
        },
        headers=headers,
    )
    assert trace.status_code == 200
    assert client.get("/v1/novaprogramming/v9/traces", headers=headers).status_code == 200

    scheduler = client.post(
        "/v1/novaprogramming/v9/assurance/scheduler/run",
        json={"organization_ids": [org_id]},
        headers=headers,
    )
    assert scheduler.status_code == 200
    assert client.get("/v1/novaprogramming/v9/assurance/scheduler/history", headers=headers).status_code == 200
