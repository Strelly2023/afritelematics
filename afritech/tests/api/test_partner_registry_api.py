from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.partner_registry_api import build_partner_registry_router
from afritech.partner_registry import PartnerRegistryStore, seed_partner_registry


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_partner_registry_router(store=PartnerRegistryStore(seed_partner_registry())))
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "operator-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_partner_registry_lists_seeded_entries() -> None:
    client = build_client()

    response = client.get("/v1/partners/registry", headers=auth_headers(role="OBSERVER", user_id="observer-1"))

    assert response.status_code == 200
    assert len(response.json()["partners"]) >= 2


def test_partner_registry_registers_partner() -> None:
    client = build_client()

    response = client.post(
        "/v1/partners/registry/register",
        json={
            "partner_id": "partner-bank-1",
            "organization": "Evidence Banking Group",
            "sector": "finance",
            "region_id": "nbo-af-east-1",
            "integration_stage": "sandbox",
            "verifier_sdk_status": "shared",
            "trust_registry_enabled": True,
        },
        headers=auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["partner_id"] == "partner-bank-1"
    assert payload["trust_registry_enabled"] is True


def test_partner_registry_advances_onboarding_state() -> None:
    client = build_client()

    response = client.post(
        "/v1/partners/registry/partner-city-ops/onboard",
        json={
            "status": "DEMO_READY",
            "integration_stage": "live corridor demo",
            "public_endpoint_enabled": True,
            "evidence_anchor_count": 2,
        },
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DEMO_READY"
    assert payload["public_endpoint_enabled"] is True
    assert payload["evidence_anchor_count"] == 2
