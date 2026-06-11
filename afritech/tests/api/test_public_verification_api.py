from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.architecture_proof_api import build_architecture_proof_router
from afritech.api.partner_registry_api import build_partner_registry_router
from afritech.api.partner_verification_api import build_partner_verification_router
from afritech.api.public_verification_api import build_public_verification_router
from afritech.api.trust_network_api import build_trust_network_router
from afritech.partner_registry import PartnerRegistryStore, seed_partner_registry
from afritech.partner_verification import PartnerVerificationStore
from afritech.standards_dependency import StandardsDependencyStore
from afritech.trust_network import TrustRegistryStore


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def build_client() -> TestClient:
    verification_store = PartnerVerificationStore()
    registry_store = TrustRegistryStore()
    dependency_store = StandardsDependencyStore()
    partner_store = PartnerRegistryStore(seed_partner_registry())
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_architecture_proof_router())
    app.include_router(build_partner_verification_router(store=verification_store))
    app.include_router(
        build_trust_network_router(
            store=registry_store,
            dependency_store=dependency_store,
            verification_store=verification_store,
        )
    )
    app.include_router(build_partner_registry_router(store=partner_store))
    app.include_router(
        build_public_verification_router(
            verification_store=verification_store,
            registry_store=registry_store,
            partner_store=partner_store,
        )
    )
    return TestClient(app)


def auth_headers(role: str = "PARTNER", user_id: str = "partner-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def publish_anchor(client: TestClient) -> str:
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
            "external_reference": "ledger-ref-public-001",
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    return response.json()["anchor_id"]


def test_public_registry_lists_published_entries() -> None:
    client = build_client()
    publish_anchor(client)

    response = client.get("/public/registry")

    assert response.status_code == 200
    assert response.json()["count"] >= 2


def test_public_verify_returns_packet_and_registry_entry() -> None:
    client = build_client()
    anchor_id = publish_anchor(client)

    response = client.get(f"/public/verify/{anchor_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["packet"]["anchor_id"] == anchor_id
    assert payload["registry_entry"]["anchor_id"] == anchor_id


def test_public_verify_resolves_architecture_proof_anchor() -> None:
    client = build_client()

    proof_response = client.get("/public/architecture/proof")
    assert proof_response.status_code == 200
    anchor_id = proof_response.json()["proof"]["verification_packet"]["anchor_id"]

    response = client.get(f"/public/verify/{anchor_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["packet"]["anchor_id"] == anchor_id
    assert payload["registry_entry"]["anchor_id"] == anchor_id


def test_public_partner_registry_filters_to_public_entries() -> None:
    client = build_client()
    client.post(
        "/v1/partners/registry/partner-city-ops/onboard",
        json={
            "status": "LIVE_CONTROLLED",
            "public_endpoint_enabled": True,
        },
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    response = client.get("/public/partners/registry")

    assert response.status_code == 200
    assert response.json()["count"] >= 1
