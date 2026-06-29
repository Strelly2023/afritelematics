from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore


def _issue_token(client: TestClient, *, role: str, organization_id: str, user_id: str) -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": user_id,
            "role": role,
            "organization_id": organization_id,
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_phase3_business_pricing_and_incentives_are_deterministic(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase3.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase3-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        customer_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-1")
        driver_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 3 Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        subscription = client.post(
            "/v1/novatech/phase0/subscriptions",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "plan": "enterprise",
                "status": "active",
                "billing_cycle": "monthly",
                "seats": 10,
            },
        )
        assert subscription.status_code == 200

        passenger_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=customer_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "balance": "0.00"},
        )
        assert passenger_wallet.status_code == 200

        wallet_credit = client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "amount": "100.00"},
        )
        assert wallet_credit.status_code == 200

        driver_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=operator_headers,
            json={"user_id": "driver-1", "currency": "AUD", "balance": "0.00"},
        )
        assert driver_wallet.status_code == 200

        driver_online = client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_headers,
            json={
                "location": {"lat": -37.8136, "lng": 144.9631, "label": "Melbourne CBD"},
                "trust_score": 96.0,
            },
        )
        assert driver_online.status_code == 200

        ride_request = client.post(
            "/v1/novaride/phase2/rides/request",
            headers=customer_headers,
            json={
                "pickup": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "destination": {"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
                "fare_estimate": "45.00",
                "currency": "AUD",
            },
        )
        assert ride_request.status_code == 200
        ride_id = ride_request.json()["ride"]["ride_id"]

        assert client.post(f"/v1/novaride/phase2/rides/{ride_id}/accept", headers=driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_id}/arrive", headers=driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_id}/start", headers=driver_headers, json={}).status_code == 200
        assert client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/complete",
            headers=driver_headers,
            json={"final_fare": "45.00"},
        ).status_code == 200

        status = client.get("/v1/novaride/phase3/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        payload = status.json()
        assert payload["view"] == "novaride_phase3_status"
        assert payload["pricing"]["ready"] is True
        assert payload["pricing"]["pricing"]["pricing_posture"] in {
            "balanced",
            "demand_rising",
            "surge_guarded",
            "discounted",
        }
        assert payload["readiness"]["pricing_verified"] is True
        assert payload["readiness"]["incentives_bounded"] is True
        assert payload["readiness"]["subscription_active"] is True
        assert payload["ready"] is True

        pricing = client.get("/v1/novaride/phase3/business/pricing", headers=operator_headers, params={"organization_id": org_id})
        assert pricing.status_code == 200
        pricing_payload = pricing.json()
        assert pricing_payload["view"] == "novaride_phase3_business_pricing"
        assert pricing_payload["pricing"]["adjusted_price"]
        assert pricing_payload["incentives"]["bounded"] is True
        assert pricing_payload["validation_report"]["verified"] is True

        incentives = client.get(
            "/v1/novaride/phase3/business/incentives",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert incentives.status_code == 200
        incentives_payload = incentives.json()
        assert incentives_payload["view"] == "novaride_phase3_business_incentives"
        assert incentives_payload["incentives"]["plan"]
        assert incentives_payload["market_signals"]["active_drivers"] >= 1
        assert incentives_payload["market_signals"]["active_rides"] >= 0

        forbidden = client.get(
            "/v1/novaride/phase3/business/pricing",
            headers=operator_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
