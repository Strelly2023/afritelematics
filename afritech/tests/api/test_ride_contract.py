"""Contract tests for completed ride evidence surfaces."""

from __future__ import annotations


def test_completed_ride_returns_receipt(client, completed_ride_id):
    response = client.get(f"/ride/{completed_ride_id}/receipt")

    assert response.status_code == 200
    body = response.json()
    assert body["ride_id"] == completed_ride_id
    assert body["receipt_id"]
    assert body["status"] == "completed"


def test_completed_ride_returns_replay(client, completed_ride_id):
    response = client.get(f"/ride/{completed_ride_id}/replay")

    assert response.status_code == 200
    body = response.json()
    assert body["ride_id"] == completed_ride_id
    assert body["replay_id"]
    assert body["replay_verified"] is True


def test_completed_ride_returns_price_explanation(client, completed_ride_id):
    response = client.get(f"/ride/{completed_ride_id}/price-explanation")

    assert response.status_code == 200
    body = response.json()
    assert body["ride_id"] == completed_ride_id
    assert body["price_explanation"]
    assert body["source"] == "core_system"
