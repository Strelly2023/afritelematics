from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT
from afritech.api.auth.jwt_device_auth import build_auth_router
from afritech.api.partner_governance_api import build_partner_governance_router
from afritech.core_platform.adaptive_sla import AdaptiveSLAController
from afritech.core_platform.autonomous_control import AutonomousControlPlane
from afritech.partner_governance import PartnerGovernanceStore, seed_partner_governance_registry


def auth_headers(role: str = "VERIFIER", user_id: str = "verifier-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


class MemoryRedis:
    def __init__(self) -> None:
        self.strings: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.strings[key] = value

    def get(self, key: str):
        return self.strings.get(key)

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.strings.pop(key, None)


def build_client(
    *,
    controller: AdaptiveSLAController | None = None,
    store: PartnerGovernanceStore | None = None,
) -> TestClient:
    app = FastAPI()
    store = store or PartnerGovernanceStore(seed_partner_governance_registry())
    app.include_router(build_auth_router())
    app.include_router(
        build_partner_governance_router(
            store=store,
            adaptive_controller=controller,
        )
    )
    return TestClient(app)


def test_partner_governance_supports_onboarding_approval_and_sla_flow() -> None:
    client = build_client()

    register = client.post(
        "/v1/trust/orgs/register",
        json={
            "org_id": "org-acme-mobility",
            "organization": "Acme Mobility",
            "country": "AU",
            "business_type": "mobility",
            "registration_number": "ACME-12345",
            "website": "https://acme.example",
            "contact_email": "platform@acme.example",
            "sla_plan": "growth",
            "permissions": ["read_logs", "sign_contract"],
            "keys": [
                {
                    "key_id": "acme-key-01",
                    "public_key": "YWNtZS1wcm9kdWN0aW9uLWtleQ==",
                    "status": "active",
                    "usage": ["contract_signing", "webhooks"],
                }
            ],
        },
        headers=auth_headers(role="OPERATOR"),
    )
    assert register.status_code == 200
    payload = register.json()
    assert payload["status"] == "pending"
    assert payload["sla_plan"] == "growth"
    assert payload["keys"][0]["key_id"] == "acme-key-01"

    review = client.post(
        "/v1/trust/orgs/org-acme-mobility/review",
        json={"reviewer_id": "verifier-9", "review_notes": "KYC in progress"},
        headers=auth_headers(role="VERIFIER"),
    )
    assert review.status_code == 200
    assert review.json()["status"] == "reviewing"
    assert review.json()["review_notes"] == "KYC in progress"

    approve = client.post(
        "/v1/trust/orgs/org-acme-mobility/approve",
        json={
            "reviewer_id": "verifier-9",
            "trust_level": "verified",
            "sla_plan": "growth",
            "permissions": ["read_logs", "sign_contract", "view_billing"],
            "review_notes": "Approved for controlled sandbox onboarding",
        },
        headers=auth_headers(role="VERIFIER"),
    )
    assert approve.status_code == 200
    approve_payload = approve.json()
    assert approve_payload["status"] == "approved"
    assert approve_payload["approval_state"] == "approved"
    assert approve_payload["activation_state"] == "inactive"
    assert approve_payload["trust_level"] == "verified"
    assert approve_payload["limits"]["plan"] == "growth"
    assert approve_payload["billing"]["plan"] == "growth"

    activate = client.post(
        "/v1/trust/orgs/org-acme-mobility/activate",
        json={"reviewer_id": "verifier-9"},
        headers=auth_headers(role="OPERATOR"),
    )
    assert activate.status_code == 200
    activate_payload = activate.json()
    assert activate_payload["status"] == "active"
    assert activate_payload["activation_state"] == "active"

    usage = client.post(
        "/v1/trust/orgs/org-acme-mobility/usage",
        json={"api_calls": 1200, "signatures": 18, "transactions": 4},
        headers=auth_headers(role="OPERATOR"),
    )
    assert usage.status_code == 200
    usage_payload = usage.json()
    assert usage_payload["usage"]["api_calls"] == 1200
    assert usage_payload["billing"]["plan"] == "growth"

    current = client.get(
        "/v1/trust/orgs/org-acme-mobility",
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert current.status_code == 200
    current_payload = current.json()
    assert current_payload["status"] == "active"
    assert current_payload["keys"][0]["key_id"] == "acme-key-01"
    assert current_payload["billing"]["estimated_cost_aud"] >= 0

    limits = client.get(
        "/v1/trust/orgs/org-acme-mobility/limits",
        headers=auth_headers(role="OBSERVER", user_id="observer-2"),
    )
    assert limits.status_code == 200
    assert limits.json()["limits"]["requests_per_min"] == 1000

    keys = client.get(
        "/v1/trust/orgs/org-acme-mobility/keys",
        headers=auth_headers(role="OBSERVER", user_id="observer-3"),
    )
    assert keys.status_code == 200
    assert keys.json()["active_key_id"] == "acme-key-01"

    billing = client.get(
        "/v1/trust/orgs/org-acme-mobility/billing",
        headers=auth_headers(role="OBSERVER", user_id="observer-4"),
    )
    assert billing.status_code == 200
    assert billing.json()["sla_state"] in {"healthy", "warning", "breached"}

    sla = client.get(
        "/v1/trust/orgs/org-acme-mobility/sla",
        headers=auth_headers(role="OBSERVER", user_id="observer-5"),
    )
    assert sla.status_code == 200
    assert sla.json()["sla_plan"] == "growth"
    assert sla.json()["enforcement_state"] in {"enabled", "throttled"}


def test_partner_governance_exposes_adaptive_sla_snapshot() -> None:
    controller = AdaptiveSLAController(client=MemoryRedis(), region="AU", default_limit=100)
    controller.observe(
        "partner-city-ops",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=45,
        observed_at=1000.0,
    )
    client = build_client(controller=controller)

    response = client.get(
        "/v1/trust/orgs/partner-city-ops/adaptive-sla",
        headers=auth_headers(role="OBSERVER", user_id="observer-6"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["org_id"] == "partner-city-ops"
    assert payload["adaptive_sla"]["mode"] == "predictive"
    assert payload["adaptive_sla"]["adjusted_limit"] >= 100
    assert payload["adaptive_sla"]["prediction"]["predicted_requests_per_min"] >= 0


def test_partner_governance_exposes_autonomous_policy_snapshot() -> None:
    redis = MemoryRedis()
    controller = AdaptiveSLAController(
        client=redis,
        region="AU",
        default_limit=100,
        autonomous_control=AutonomousControlPlane(client=redis),
    )
    controller.observe(
        "partner-city-ops",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=200,
        observed_at=1000.0,
    )
    client = build_client(controller=controller)

    response = client.get(
        "/v1/trust/orgs/partner-city-ops/adaptive-sla",
        headers=auth_headers(role="OBSERVER", user_id="observer-7"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["adaptive_sla"]["autonomy"]["action"] in {"maintain", "decrease_limit", "increase_limit", "hold"}
    assert "limit_multiplier" not in payload["adaptive_sla"]["autonomy"]


def test_partner_governance_rejects_unknown_organization() -> None:
    client = build_client()

    response = client.get(
        "/v1/trust/orgs/unknown-org",
        headers=auth_headers(role="OBSERVER", user_id="observer-5"),
    )

    assert response.status_code == 404
