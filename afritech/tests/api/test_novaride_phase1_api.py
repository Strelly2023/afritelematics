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


def test_phase1_ride_lifecycle_and_wallet_settlement(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase1.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase1-001"

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
                "legal_name": "Phase 1 Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        status = client.get("/v1/novaride/phase1/status", headers=customer_headers)
        assert status.status_code == 200
        assert status.json()["ready"] is False

        wallet_create = client.post(
            "/v1/novaride/phase1/wallets",
            headers=customer_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "balance": "0.00"},
        )
        assert wallet_create.status_code == 200

        wallet_credit = client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "amount": "100.00"},
        )
        assert wallet_credit.status_code == 200
        assert wallet_credit.json()["wallet"]["balance"] == "100.00"

        ride_request = client.post(
            "/v1/novaride/phase1/rides/request",
            headers=customer_headers,
            json={
                "pickup": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "destination": {"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
                "fare_estimate": "25.00",
                "currency": "AUD",
            },
        )
        assert ride_request.status_code == 200
        ride_id = ride_request.json()["ride"]["ride_id"]

        trip_start = client.post(
            f"/v1/novaride/phase1/rides/{ride_id}/start",
            headers=driver_headers,
            json={},
        )
        assert trip_start.status_code == 200
        assert trip_start.json()["ride"]["status"] == "in_progress"

        trip_complete = client.post(
            f"/v1/novaride/phase1/rides/{ride_id}/complete",
            headers=driver_headers,
            json={"final_fare": "25.00"},
        )
        assert trip_complete.status_code == 200
        assert trip_complete.json()["ride"]["status"] == "completed"
        assert len(trip_complete.json()["payment"]["transactions"]) == 2

        ride_detail = client.get(f"/v1/novaride/phase1/rides/{ride_id}", headers=customer_headers)
        assert ride_detail.status_code == 200
        assert ride_detail.json()["ride"]["status"] == "completed"

        wallets = client.get("/v1/novaride/phase1/wallets", headers=operator_headers, params={"organization_id": org_id})
        assert wallets.status_code == 200
        wallet_map = {wallet["user_id"]: wallet for wallet in wallets.json()["wallets"]}
        assert wallet_map["passenger-1"]["balance"] == "75.00"
        assert wallet_map["driver-1"]["balance"] == "25.00"

        transactions = client.get("/v1/novaride/phase1/transactions", headers=operator_headers, params={"organization_id": org_id, "ride_id": ride_id})
        assert transactions.status_code == 200
        assert len(transactions.json()["transactions"]) == 2

        events = client.get("/v1/novaride/phase1/events", headers=operator_headers, params={"organization_id": org_id, "limit": 20})
        assert events.status_code == 200
        assert len(events.json()["events"]) >= 4

        refreshed = client.get("/v1/novaride/phase1/status", headers=customer_headers)
        assert refreshed.status_code == 200
        refreshed_payload = refreshed.json()
        assert refreshed_payload["readiness"]["ride_lifecycle_runs"] is True
        assert refreshed_payload["readiness"]["events_stored"] is True
        assert refreshed_payload["readiness"]["wallet_updates"] is True
        assert refreshed_payload["readiness"]["transactions_recorded"] is True
        assert refreshed_payload["readiness"]["payments_automated"] is True
        assert refreshed_payload["readiness"]["all_actions_audited"] is True
        assert refreshed_payload["readiness"]["tenant_isolation_preserved"] is True
        assert refreshed_payload["ready"] is True
    finally:
        control_plane._STORE = original_store
