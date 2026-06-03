"""Driver backend contract tests.

These tests verify that the backend contract exposes the evidence
surfaces required by the Driver App.

The backend may authorize:
- assigned ride visibility
- accept/start/complete transitions
- receipt evidence
- replay evidence
- earnings evidence

The Driver App must only consume these surfaces.
It must not create pricing, dispatch, replay, receipt, or earnings authority.
"""

from __future__ import annotations


def test_driver_can_fetch_assigned_rides(client):
    response = client.get("/driver/driver-1/rides/assigned")

    assert response.status_code == 200

    body = response.json()

    assert "rides" in body
    assert isinstance(body["rides"], list)

    ride = body["rides"][0]

    assert ride["ride_id"]
    assert ride["pickup"]
    assert ride["dropoff"]
    assert ride["status"] == "assigned"
    assert ride["assigned_driver_id"] == "driver-1"


def test_driver_can_accept_ride_through_contract(client):
    response = client.post(
        "/ride/ride-1/accept",
        json={
            "driver_id": "driver-1",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["ok"] is True
    assert body["ride_id"] == "ride-1"
    assert body["driver_id"] == "driver-1"
    assert body["action"] == "accept"


def test_driver_can_start_ride_through_contract(client):
    response = client.post(
        "/ride/ride-1/start",
        json={
            "driver_id": "driver-1",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["ok"] is True
    assert body["ride_id"] == "ride-1"
    assert body["driver_id"] == "driver-1"
    assert body["action"] == "start"


def test_driver_can_complete_ride_through_contract(client):
    response = client.post(
        "/ride/ride-1/complete",
        json={
            "driver_id": "driver-1",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["ok"] is True
    assert body["ride_id"] == "ride-1"
    assert body["driver_id"] == "driver-1"
    assert body["action"] == "complete"


def test_driver_completed_ride_returns_receipt_evidence(client):
    response = client.get("/ride/ride-1/receipt")

    assert response.status_code == 200

    body = response.json()

    assert body["ride_id"] == "ride-1"
    assert body["receipt_id"]
    assert body["status"] == "completed"
    assert body["replay_id"]
    assert body["receipt_hash"]
    assert body["issued_at"]


def test_driver_completed_ride_returns_replay_evidence(client):
    response = client.get("/ride/ride-1/replay")

    assert response.status_code == 200

    body = response.json()

    assert body["ride_id"] == "ride-1"
    assert body["replay_id"]
    assert body["replay_verified"] is True
    assert body["replay_hash"]
    assert body["receipt_id"]
    assert body["replay_epoch"] >= 0


def test_driver_can_fetch_earnings_evidence(client):
    response = client.get("/driver/driver-1/earnings")

    assert response.status_code == 200

    body = response.json()

    assert body["driver_id"] == "driver-1"
    assert body["daily_total"] >= 0
    assert body["weekly_total"] >= 0
    assert body["earnings_receipt_id"]
    assert body["earnings_period_id"]
    assert body["replay_verified"] is True


def test_driver_rejects_mismatched_driver_for_action(client):
    response = client.post(
        "/ride/ride-1/accept",
        json={
            "driver_id": "driver-999",
        },
    )

    assert response.status_code in {403, 409}

    body = response.json()

    assert body["error"] in {
        "driver_assignment_mismatch",
        "forbidden_driver_assignment",
    }


def test_driver_backend_contract_exposes_no_pricing_authority(client):
    response = client.post(
        "/ride/ride-1/calculate_price",
        json={
            "driver_id": "driver-1",
        },
    )

    assert response.status_code in {404, 405}


def test_driver_backend_contract_exposes_no_replay_mutation(client):
    response = client.post(
        "/ride/ride-1/replay",
        json={
            "driver_id": "driver-1",
            "replay_verified": True,
        },
    )

    assert response.status_code in {404, 405}