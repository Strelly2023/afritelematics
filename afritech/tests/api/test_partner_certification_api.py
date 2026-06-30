from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT


def auth_headers(
    role: str = "VERIFIER",
    user_id: str = "verifier-1",
    org_id: str = "partner-city-ops",
) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {
        "Authorization": f"Bearer {token}",
        "X-Org-ID": org_id,
    }


def test_partner_certification_flow_verifies_contract_and_supports_registry_lookup() -> None:
    client = TestClient(app)

    certify = client.post(
        "/v1/partners/partner-city-ops/certify",
        json={
            "supported_versions": ["2026.07", "2026.07.0"],
            "capabilities": ["sdk_registry", "compatibility_matrix"],
            "sdk_language": "python",
        },
        headers=auth_headers(),
    )
    assert certify.status_code == 200
    certificate = certify.json()
    assert certificate["partner_id"] == "partner-city-ops"
    assert certificate["status"] == "CERTIFIED"
    assert certificate["verification"]["signature_valid"] is True
    assert certificate["verification"]["contract_valid"] is True
    assert certificate["verification"]["supported_versions_valid"] is True
    assert certificate["verification"]["sdk_compatibility_valid"] is True

    lookup = client.get(
        "/v1/partners/partner-city-ops/certificate",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert lookup.status_code == 200
    assert lookup.json()["certificate_id"] == certificate["certificate_id"]

    verification = client.get(
        "/v1/partners/partner-city-ops/verification",
        headers=auth_headers(role="OBSERVER", user_id="observer-2"),
    )
    assert verification.status_code == 200
    payload = verification.json()
    assert payload["status"] == "CERTIFIED"
    assert payload["verification"]["signature_valid"] is True
    assert payload["verification"]["contract_valid"] is True


def test_partner_certification_rejects_unknown_partner_lookup() -> None:
    client = TestClient(app)

    response = client.get(
        "/v1/partners/unknown/certificate",
        headers=auth_headers(role="OBSERVER", user_id="observer-3", org_id="unknown"),
    )

    assert response.status_code == 404


def test_partner_certification_rejects_unknown_partner_certification() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/partners/unknown/certify",
        json={"supported_versions": ["2026.07.0"]},
        headers=auth_headers(org_id="unknown"),
    )

    assert response.status_code == 404
