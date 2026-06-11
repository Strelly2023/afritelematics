from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.partner_verification_api import build_partner_verification_router


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_partner_verification_router())
    return TestClient(app)


def auth_headers(role: str = "PARTNER", user_id: str = "partner-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_partner_verify_returns_replay_linked_packet() -> None:
    client = build_client()

    response = client.post(
        "/v1/partner/verify",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
            "external_reference": "ledger-ref-001",
        },
        headers=auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["verification_status"] == "VERIFIED"
    assert body["authority_boundary"] == (
        "trace records authority; replay reconstructs truth; "
        "anchor proves export integrity only"
    )
    assert body["publication_target"] == "public-ledger-test-anchor"
    assert body["anchor_id"].startswith("anchor-")
    assert body["authority_hash"] == HASH_D
    assert body["execution_fingerprint"] == HASH_E


def test_partner_anchor_lookup_returns_saved_packet() -> None:
    client = build_client()
    created = client.post(
        "/v1/partner/verify",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
            "external_reference": "ledger-ref-lookup-001",
        },
        headers=auth_headers(),
    )
    anchor_id = created.json()["anchor_id"]

    response = client.get(
        f"/v1/partner/anchors/{anchor_id}",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )

    assert response.status_code == 200
    assert response.json()["anchor_id"] == anchor_id


def test_partner_verify_rejects_mismatched_expectation() -> None:
    client = build_client()

    response = client.post(
        "/v1/partner/verify",
        json={
            "tenant_id": "tenant-core",
            "region_id": "mel-ap-southeast-2",
            "trace_hash": HASH_A,
            "replay_hash": HASH_B,
            "receipt_hash": HASH_C,
            "authority_hash": HASH_D,
            "execution_fingerprint": HASH_E,
            "publication_target": "public-ledger-test-anchor",
            "expected_anchor_id": "anchor-wrong",
        },
        headers=auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["verification_status"] == "REJECTED"
    assert "anchor_id_mismatch" in body["mismatch_reasons"]


def test_partner_verify_requires_fields() -> None:
    client = build_client()

    response = client.post(
        "/v1/partner/verify",
        json={
            "tenant_id": "tenant-core",
        },
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert "missing field" in response.json()["detail"]
