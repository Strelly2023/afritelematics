from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.feature_registry_api import (
    FeatureRegistryPayloadSchema,
    build_feature_registry_router,
)
from afritech.tools.feature_registry_verifier import verify_registry_payload


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_feature_registry_router())
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "operator-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_feature_registry_requires_operator_auth():
    client = build_client()

    response = client.get("/api/feature-registry")

    assert response.status_code in {401, 403}


def test_feature_registry_endpoint_returns_governed_payload():
    client = build_client()

    response = client.get("/api/feature-registry", headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"
    assert payload["status"] == "FEATURE_REGISTRY_LEVEL_12"
    assert payload["generation_mode"] == "REPLAY_DERIVED_EVIDENCE_PROJECTION"
    assert payload["read_only"] is True
    assert payload["creates_authority"] is False
    assert payload["feature_count"] == 15
    assert payload["complete_feature_count"] == 15
    assert payload["candidate_feature_count"] == 15
    assert payload["production_ready_feature_count"] == 3
    assert payload["production_ready_feature_ids"] == [
        "driver-identity-proof",
        "trip-integrity-proof",
        "payment-proof-anchor",
    ]
    assert payload["verified_true"] is True
    assert payload["live_pilot_authorized"] is False
    assert payload["registry_hash"]
    assert payload["signature"]["algorithm"] == "Ed25519"
    assert verify_registry_payload(payload)["verified"] is True
    assert payload["features"][0]["id"] == "trust-kernel"
    assert payload["features"][0]["evidence_complete"] is True
    assert FeatureRegistryPayloadSchema(**payload).classification == (
        "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"
    )


def test_feature_registry_v1_alias_matches_requested_endpoint():
    client = build_client()
    headers = auth_headers()

    requested = client.get("/api/feature-registry", headers=headers).json()
    versioned = client.get("/v1/feature-registry", headers=headers).json()

    assert versioned == requested


def test_public_feature_registry_partner_validation_surfaces():
    client = build_client()

    registry_response = client.get("/public/feature-registry")
    verify_response = client.get("/public/feature-registry/verify")
    portal_response = client.get("/public/feature-registry/portal")

    assert registry_response.status_code == 200
    assert registry_response.json()["classification"] == "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"
    assert verify_response.status_code == 200
    assert verify_response.json()["verified"] is True
    assert verify_response.json()["federated_trust"]["verified"] is True
    assert verify_response.json()["verified_true"] is True
    assert verify_response.json()["no_fake_feature_can_exist"] is True
    assert portal_response.status_code == 200
    assert "AfriTech Feature Registry Trust Portal" in portal_response.text
    assert "No fake feature can exist" in portal_response.text
    assert "/public/feature-registry/verify" in portal_response.text
    assert "/public/trust-infrastructure/verify" in portal_response.text
    assert "/public/global-verification/verify" in portal_response.text


def test_public_trust_badge_system_exports_shareable_proof():
    client = build_client()

    badge = client.get("/public/trust-badge")
    feature_badge = client.get("/public/trust-badge/trip-integrity-proof")
    badge_html = client.get("/public/trust-badge/trip-integrity-proof/html")

    assert badge.status_code == 200
    assert badge.json()["classification"] == "AFRITECH_PUBLIC_TRUST_BADGE"
    assert badge.json()["label"] == "Verified by AfriTech Trust Layer"
    assert badge.json()["verified"] is True
    assert badge.json()["verified_true"] is True
    assert badge.json()["verification"]["verified"] is True
    assert feature_badge.status_code == 200
    assert feature_badge.json()["feature"]["id"] == "trip-integrity-proof"
    assert feature_badge.json()["links"]["system_integrity"] == "/public/ecosystem-evolution/verify"
    assert badge_html.status_code == 200
    assert "Verified by AfriTech Trust Layer" in badge_html.text
    assert "Verify system integrity" in badge_html.text


def test_public_trust_infrastructure_surfaces_for_partners_and_governments():
    client = build_client()

    certificate = client.get("/public/trust-infrastructure")
    verification = client.get("/public/trust-infrastructure/verify")

    assert certificate.status_code == 200
    assert certificate.json()["classification"] == "LEVEL_14_FEDERATED_TRUST_NETWORK"
    assert certificate.json()["verification"]["partner_ready"] is True
    assert certificate.json()["verification"]["public_sector_ready"] is True
    assert verification.status_code == 200
    assert verification.json()["verified"] is True
    assert verification.json()["guarantees"]["no_untrusted_party_can_sign_truth"] is True
    assert verification.json()["guarantees"]["federated_quorum_required"] is True


def test_public_global_verification_layer_surfaces_exportable_truth():
    client = build_client()

    bundle = client.get("/public/global-verification")
    verification = client.get("/public/global-verification/verify")
    portal = client.get("/public/global-verification/portal")

    assert bundle.status_code == 200
    assert bundle.json()["classification"] == "LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER"
    assert bundle.json()["level"] == "LEVEL_15"
    assert bundle.json()["optional_onchain_anchor_supported"] is True
    assert verification.status_code == 200
    assert verification.json()["verified"] is True
    assert verification.json()["cross_network"]["network_count"] >= 3
    assert verification.json()["guarantees"]["truth_independent_of_origin_system"] is True
    assert verification.json()["guarantees"]["no_production_state_can_be_falsely_implied"] is True
    assert portal.status_code == 200
    assert "AfriTech Global Public Verification Layer" in portal.text
    assert "/public/global-verification/verify" in portal.text


def test_public_ecosystem_evolution_surfaces_level16_adoption_layer():
    client = build_client()

    certificate = client.get("/public/ecosystem-evolution")
    verification = client.get("/public/ecosystem-evolution/verify")
    standard = client.get("/public/ecosystem-evolution/standard")
    portal = client.get("/public/ecosystem-evolution/portal")

    assert certificate.status_code == 200
    assert certificate.json()["classification"] == "LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE"
    assert certificate.json()["level"] == "LEVEL_16"
    assert verification.status_code == 200
    assert verification.json()["verified"] is True
    assert verification.json()["organizations"]["organization_count"] >= 3
    assert verification.json()["government_adoption"]["government_profile_count"] >= 2
    assert verification.json()["live_public_ledger_anchoring"]["verified"] is True
    assert verification.json()["interoperable_standard"]["verified"] is True
    assert standard.status_code == 200
    assert standard.json()["standard_id"] == "AFRITECH_GLOBAL_TRUST_INTEROPERABILITY_STANDARD"
    assert "/public/ecosystem-evolution/verify" in standard.json()["required_surfaces"]
    assert portal.status_code == 200
    assert "AfriTech Ecosystem Trust Infrastructure" in portal.text
    assert "/public/ecosystem-evolution/standard" in portal.text


def test_live_ecosystem_anchor_requires_operator_auth():
    client = build_client()

    response = client.post(
        "/api/ecosystem-evolution/anchor/live",
        json={"profile": "sepolia", "require_live": False},
    )

    assert response.status_code in {401, 403}


def test_feature_registry_openapi_contract_is_locked():
    client = build_client()

    schema = client.app.openapi()
    route = schema["paths"]["/api/feature-registry"]["get"]
    encoded = str(route)

    assert "FeatureRegistryPayloadSchema" in encoded
    assert "feature-registry" in route["tags"]
