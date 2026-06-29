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


def test_phase4_city_budget_allocation_and_profit_optimization_are_deterministic(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase4.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase4-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        passenger_1_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-1")
        passenger_2_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-2")
        driver_1_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        driver_2_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-2")
        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        passenger_1_headers = {"Authorization": f"Bearer {passenger_1_token}"}
        passenger_2_headers = {"Authorization": f"Bearer {passenger_2_token}"}
        driver_1_headers = {"Authorization": f"Bearer {driver_1_token}"}
        driver_2_headers = {"Authorization": f"Bearer {driver_2_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 4 Mobility Pty Ltd",
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
                "seats": 12,
            },
        )
        assert subscription.status_code == 200

        assert client.post(
            "/v1/novaride/phase1/wallets",
            headers=passenger_1_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "balance": "0.00"},
        ).status_code == 200
        assert client.post(
            "/v1/novaride/phase1/wallets",
            headers=passenger_2_headers,
            json={"user_id": "passenger-2", "currency": "AUD", "balance": "0.00"},
        ).status_code == 200
        assert client.post(
            "/v1/novaride/phase1/wallets",
            headers=operator_headers,
            json={"user_id": "driver-1", "currency": "AUD", "balance": "0.00"},
        ).status_code == 200
        assert client.post(
            "/v1/novaride/phase1/wallets",
            headers=operator_headers,
            json={"user_id": "driver-2", "currency": "AUD", "balance": "0.00"},
        ).status_code == 200

        assert client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "amount": "100.00"},
        ).status_code == 200
        assert client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-2", "currency": "AUD", "amount": "100.00"},
        ).status_code == 200

        assert client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_1_headers,
            json={
                "location": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "trust_score": 98.0,
            },
        ).status_code == 200
        assert client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_2_headers,
            json={
                "location": {"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
                "trust_score": 90.0,
            },
        ).status_code == 200

        ride_1 = client.post(
            "/v1/novaride/phase2/rides/request",
            headers=passenger_1_headers,
            json={
                "pickup": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "destination": {"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
                "fare_estimate": "40.00",
                "currency": "AUD",
            },
        )
        assert ride_1.status_code == 200
        ride_1_id = ride_1.json()["ride"]["ride_id"]
        ride_1_driver_id = ride_1.json()["dispatch"]["ride"]["driver_id"]
        assert ride_1_driver_id in {"driver-1", "driver-2"}

        ride_2 = client.post(
            "/v1/novaride/phase2/rides/request",
            headers=passenger_2_headers,
            json={
                "pickup": {"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
                "destination": {"lat": -37.8200, "lng": 144.9800, "label": "Richmond"},
                "fare_estimate": "35.00",
                "currency": "AUD",
            },
        )
        assert ride_2.status_code == 200
        ride_2_id = ride_2.json()["ride"]["ride_id"]
        ride_2_driver_id = ride_2.json()["dispatch"]["ride"]["driver_id"]
        assert ride_2_driver_id in {"driver-1", "driver-2"}

        driver_headers = {
            "driver-1": driver_1_headers,
            "driver-2": driver_2_headers,
        }
        ride_1_driver_headers = driver_headers[ride_1_driver_id]
        ride_2_driver_headers = driver_headers[ride_2_driver_id]
        assert client.post(f"/v1/novaride/phase2/rides/{ride_1_id}/accept", headers=ride_1_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_1_id}/arrive", headers=ride_1_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_1_id}/start", headers=ride_1_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_1_id}/complete", headers=ride_1_driver_headers, json={"final_fare": "40.00"}).status_code == 200

        assert client.post(f"/v1/novaride/phase2/rides/{ride_2_id}/accept", headers=ride_2_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_2_id}/arrive", headers=ride_2_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_2_id}/start", headers=ride_2_driver_headers, json={}).status_code == 200
        assert client.post(f"/v1/novaride/phase2/rides/{ride_2_id}/complete", headers=ride_2_driver_headers, json={"final_fare": "35.00"}).status_code == 200

        status = client.get("/v1/novaride/phase4/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["view"] == "novaride_phase4_status"
        assert status_payload["readiness"]["phase3_ready"] is True
        assert status_payload["readiness"]["budget_allocation_verified"] is True
        assert status_payload["readiness"]["profit_optimization_verified"] is True
        assert status_payload["ready"] is True

        allocation = client.get(
            "/v1/novaride/phase4/business/budget-allocation",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert allocation.status_code == 200
        allocation_payload = allocation.json()
        assert allocation_payload["view"] == "novaride_phase4_budget_allocation"
        assert allocation_payload["budget_allocation"]["mode"] in {"autonomous", "supervised", "held"}
        assert len(allocation_payload["budget_allocation"]["city_allocations"]) >= 2
        assert {item["city"] for item in allocation_payload["budget_allocation"]["city_allocations"]} >= {"CBD", "Southbank"}
        assert allocation_payload["budget_allocation"]["budget_pool"] != "0.00"

        profit = client.get(
            "/v1/novaride/phase4/business/profit-optimization",
            headers=operator_headers,
            params={"organization_id": org_id},
        )
        assert profit.status_code == 200
        profit_payload = profit.json()
        assert profit_payload["view"] == "novaride_phase4_profit_optimization"
        assert profit_payload["profit_optimization"]["projected_profit"]
        assert profit_payload["profit_optimization"]["optimization_actions"]
        assert profit_payload["city_signals"]["city_count"] >= 2

        forbidden = client.get(
            "/v1/novaride/phase4/business/budget-allocation",
            headers=operator_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
