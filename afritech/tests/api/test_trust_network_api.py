from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.trust_network_api import build_trust_network_router


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_trust_network_router())
    return TestClient(app)


def auth_headers(role: str = "PARTNER", user_id: str = "partner-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_publish_trust_registry_entry() -> None:
    client = build_client()
    response = client.post(
        "/v1/trust/registry/publish",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
            "external_reference": "ledger-ref-registry-001",
        },
        headers=auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["registry_id"].startswith("registry-")
    assert body["authority_boundary"] == "registry_indexes_evidence_only"


def test_list_registry_returns_published_entries() -> None:
    client = build_client()
    client.post(
        "/v1/trust/registry/publish",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
        },
        headers=auth_headers(),
    )

    response = client.get("/v1/trust/registry", headers=auth_headers(role="OBSERVER", user_id="observer-1"))

    assert response.status_code == 200
    assert len(response.json()["entries"]) == 1


def test_register_and_list_dependents() -> None:
    client = build_client()
    created = client.post(
        "/v1/trust/dependents/register",
        json={
            "dependent_id": "partner-a-core",
            "organization": "Partner A",
            "use_case": "claims validation",
        },
        headers=auth_headers(),
    )

    assert created.status_code == 200
    assert created.json()["status"] == "DECLARED_DEPENDENCY"

    listing = client.get("/v1/trust/dependents", headers=auth_headers(role="OBSERVER", user_id="observer-1"))
    assert listing.status_code == 200
    assert len(listing.json()["dependents"]) == 1


def test_standard_profile_surface_is_exposed() -> None:
    client = build_client()
    response = client.get("/v1/trust/standards/profile")

    assert response.status_code == 200
    assert response.json()["profile_id"] == "MULTI_PARTY_REPLAY_VERIFICATION_V1"


def test_verify_network_returns_registry_and_quorum_record() -> None:
    client = build_client()
    client.post(
        "/v1/trust/dependents/register",
        json={
            "dependent_id": "partner-a-core",
            "organization": "Partner A",
            "use_case": "claims validation",
        },
        headers=auth_headers(),
    )
    response = client.post(
        "/v1/trust/network/verify",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
            "witnesses": [
                {
                    "verifier_id": "v1",
                    "organization": "partner-a",
                    "decision": "VERIFIED",
                    "evidence_hash": "0" * 64,
                },
                {
                    "verifier_id": "v2",
                    "organization": "partner-b",
                    "decision": "VERIFIED",
                    "evidence_hash": "1" * 64,
                },
            ],
            "quorum": 2,
        },
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["registry_entry"]["anchor_id"].startswith("anchor-")
    assert body["registry_entry"]["dependent_system_count"] == 1
    assert body["verification_network"]["aggregate_status"] == "QUORUM_VERIFIED"
    assert body["verification_network"]["dependent_system_count"] == 1
    assert len(body["witness_manifest_hash"]) == 64
