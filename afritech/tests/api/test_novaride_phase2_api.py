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


def test_phase2_real_time_dispatch_driver_presence_and_external_payment(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase2.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase2-001"

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
                "legal_name": "Phase 2 Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        passenger_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=customer_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "balance": "0.00"},
        )
        assert passenger_wallet.status_code == 200

        driver_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=operator_headers,
            json={"user_id": "driver-1", "currency": "AUD", "balance": "0.00"},
        )
        assert driver_wallet.status_code == 200

        wallet_credit = client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "amount": "100.00"},
        )
        assert wallet_credit.status_code == 200

        driver_online = client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_headers,
            json={
                "location": {"lat": -37.8136, "lng": 144.9631, "label": "Melbourne CBD"},
                "trust_score": 91.0,
            },
        )
        assert driver_online.status_code == 200
        assert driver_online.json()["presence"]["status"] == "online"

        ride_request = client.post(
            "/v1/novaride/phase2/rides/request",
            headers=customer_headers,
            json={
                "pickup": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "destination": {"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
                "fare_estimate": "30.00",
                "currency": "AUD",
            },
        )
        assert ride_request.status_code == 200
        ride_payload = ride_request.json()
        ride_id = ride_payload["ride"]["ride_id"]
        assert ride_payload["dispatch"]["ride"]["driver_id"] == "driver-1"
        payment_authorization = ride_payload["dispatch"]["payment_authorization"]
        assert payment_authorization["authorization"]["provider"] == "payid"
        assert payment_authorization["provider_result"]["mode"] == "controlled_rehearsal"
        assert payment_authorization["provider_result"]["live_network_called"] is False

        accept = client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/accept",
            headers=driver_headers,
            json={},
        )
        assert accept.status_code == 200
        assert accept.json()["presence"]["status"] == "busy"

        arrive = client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/arrive",
            headers=driver_headers,
            json={},
        )
        assert arrive.status_code == 200
        assert arrive.json()["ride"]["status"] == "arrived"

        start = client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/start",
            headers=driver_headers,
            json={},
        )
        assert start.status_code == 200
        assert start.json()["payload"]["ride"]["status"] == "in_progress"

        complete = client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/complete",
            headers=driver_headers,
            json={"final_fare": "30.00"},
        )
        assert complete.status_code == 200
        assert complete.json()["payment"]["capture"]["status"] == "captured"
        assert complete.json()["payment"]["authorization"]["capture_status"] == "captured"

        wallets = client.get("/v1/novaride/phase1/wallets", headers=operator_headers, params={"organization_id": org_id})
        assert wallets.status_code == 200
        wallet_map = {wallet["user_id"]: wallet for wallet in wallets.json()["wallets"]}
        assert wallet_map["passenger-1"]["balance"] == "70.00"
        assert wallet_map["driver-1"]["balance"] == "30.00"

        transactions = client.get(
            "/v1/novaride/phase1/transactions",
            headers=operator_headers,
            params={"organization_id": org_id, "ride_id": ride_id},
        )
        assert transactions.status_code == 200
        assert len(transactions.json()["transactions"]) == 2

        payments = client.get(
            "/v1/novaride/phase2/payments",
            headers=operator_headers,
            params={"organization_id": org_id, "ride_id": ride_id},
        )
        assert payments.status_code == 200
        assert payments.json()["authorizations"][0]["capture_status"] == "captured"
        assert len(payments.json()["captures"]) == 1

        status = client.get("/v1/novaride/phase2/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        payload = status.json()
        assert payload["readiness"]["drivers_online"] is True
        assert payload["readiness"]["dispatch_assigned"] is True
        assert payload["readiness"]["ride_assigned"] is True
        assert payload["readiness"]["driver_acceptance_recorded"] is True
        assert payload["readiness"]["driver_arrival_recorded"] is True
        assert payload["readiness"]["trip_started"] is True
        assert payload["readiness"]["external_payment_authorized"] is True
        assert payload["readiness"]["payment_captured"] is True
        assert payload["readiness"]["ledger_updated"] is True
        assert payload["readiness"]["tenant_isolation_preserved"] is True
        assert payload["ready"] is True

        forbidden = client.get(
            "/v1/novaride/phase2/rides",
            headers=operator_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store


def test_phase2_bounded_autonomous_dispatch_reports_driver_allocation(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase2-autonomy.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase2-autonomy-001"

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
                "legal_name": "Autonomy Dispatch Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        passenger_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=customer_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "balance": "0.00"},
        )
        assert passenger_wallet.status_code == 200

        driver_wallet = client.post(
            "/v1/novaride/phase1/wallets",
            headers=operator_headers,
            json={"user_id": "driver-1", "currency": "AUD", "balance": "0.00"},
        )
        assert driver_wallet.status_code == 200

        client.post(
            "/v1/novaride/phase1/wallets/credit",
            headers=operator_headers,
            json={"user_id": "passenger-1", "currency": "AUD", "amount": "100.00"},
        )

        driver_online = client.post(
            "/v1/novaride/phase2/drivers/online",
            headers=driver_headers,
            json={
                "location": {"lat": -37.8136, "lng": 144.9631, "label": "Melbourne CBD"},
                "trust_score": 91.0,
            },
        )
        assert driver_online.status_code == 200

        ride_request = client.post(
            "/v1/novaride/phase1/rides/request",
            headers=customer_headers,
            json={
                "pickup": {"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
                "destination": {"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
                "fare_estimate": "30.00",
                "currency": "AUD",
            },
        )
        assert ride_request.status_code == 200
        ride_id = ride_request.json()["ride"]["ride_id"]

        autonomous = client.post(
            f"/v1/novaride/phase2/rides/{ride_id}/autonomous-dispatch",
            headers=operator_headers,
            json={},
        )
        assert autonomous.status_code == 200
        payload = autonomous.json()
        assert payload["autonomy"]["mode"] in {"advisory", "supervised", "autonomous", "fully_autonomous"}
        assert "safe_to_autorun" in payload["autonomy"]
        assert "driver_allocation" in payload
        assert payload["driver_allocation"]["selected_driver_id"] == "driver-1"
        assert payload["driver_allocation"]["available_drivers"] >= 1
        assert payload["executed"] is False
        assert payload["held_reason"]
        assert "reason" in payload["driver_allocation"]
    finally:
        control_plane._STORE = original_store
