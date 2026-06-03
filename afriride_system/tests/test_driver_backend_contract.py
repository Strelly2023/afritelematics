from __future__ import annotations

from fastapi.testclient import TestClient

from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app


def test_driver_app_backend_contract_completes_replay_visible_lifecycle() -> None:
    reset_gateway()
    client = TestClient(app)

    driver_status = client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": "driver-contract-online"},
    )
    assert driver_status.status_code == 200

    request = client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-contract-1",
        },
        headers={"Idempotency-Key": "driver-contract-request"},
    )
    assert request.status_code == 200

    assigned = client.get("/driver/driver-1/rides/assigned")
    assert assigned.status_code == 200
    assigned_payload = assigned.json()
    assert assigned_payload["rides"] == [
        {
            "ride_id": "ride-contract-1",
            "pickup": "Kampala Road",
            "dropoff": "Nakasero",
            "status": "assigned",
            "assigned_driver_id": "driver-1",
            "receipt_id": None,
            "replay_id": None,
        }
    ]

    accepted = client.post(
        "/ride/ride-contract-1/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "driver-contract-accept"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "DRIVER_ASSIGNED"

    started = client.post(
        "/ride/ride-contract-1/start",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "driver-contract-start"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "IN_TRIP"

    completed = client.post(
        "/ride/ride-contract-1/complete",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "driver-contract-complete"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    receipt = client.get("/ride/ride-contract-1/receipt")
    assert receipt.status_code == 200
    receipt_payload = receipt.json()
    assert receipt_payload["ride_id"] == "ride-contract-1"
    assert receipt_payload["receipt_id"] == "receipt-ride-contract-1"
    assert receipt_payload["status"] == "completed"
    assert len(receipt_payload["receipt_hash"]) == 64

    replay = client.get("/ride/ride-contract-1/replay")
    assert replay.status_code == 200
    replay_payload = replay.json()
    assert replay_payload["ride_id"] == "ride-contract-1"
    assert replay_payload["replay_verified"] is True
    assert replay_payload["receipt_id"] == receipt_payload["receipt_id"]
    assert len(replay_payload["replay_hash"]) == 64

    ledger_receipt = client.get("/ride/ride-contract-1/ledger-receipt")
    assert ledger_receipt.status_code == 200
    ledger_payload = ledger_receipt.json()
    assert ledger_payload["receipt_id"] == "ledger-receipt-ride-contract-1"
    assert ledger_payload["verdict"] == "VALID"
    assert ledger_payload["ledger_proof"]["event_count"] == 7
    assert ledger_payload["ledger_proof"]["hash_mode"] == "sha256_canonical_chain"
    assert ledger_payload["signature_validation"]["signature_mode"] == "rsa_pss_sha256"
    assert ledger_payload["signature_validation"]["all_signatures_valid"] is True
    assert ledger_payload["identity_validation"]["all_verified"] is True
    assert ledger_payload["replay_proof"]["replay_valid"] is True
    assert len(ledger_payload["receipt_hash"]) == 64

    earnings = client.get("/driver/driver-1/earnings")
    assert earnings.status_code == 200
    earnings_payload = earnings.json()
    assert earnings_payload["driver_id"] == "driver-1"
    assert earnings_payload["daily_total"] >= 0
    assert earnings_payload["replay_verified"] is True


def test_rider_backend_driver_loop_exposes_same_derived_proof_to_rider() -> None:
    reset_gateway()
    client = TestClient(app)

    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": "rider-loop-driver-online"},
    )
    requested = client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-rider-loop-1",
        },
        headers={"Idempotency-Key": "rider-loop-request"},
    )
    assert requested.status_code == 200

    client.post(
        "/ride/ride-rider-loop-1/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "rider-loop-accept"},
    )
    client.post(
        "/ride/ride-rider-loop-1/start",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "rider-loop-start"},
    )
    client.post(
        "/ride/ride-rider-loop-1/complete",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "rider-loop-complete"},
    )

    rider_status = client.get("/passenger/status/ride-rider-loop-1")
    assert rider_status.status_code == 200
    assert rider_status.json()["data"]["status"] == "COMPLETED"

    rider_receipt = client.get("/ride/ride-rider-loop-1/receipt")
    rider_replay = client.get("/ride/ride-rider-loop-1/replay")
    rider_ledger_receipt = client.get("/ride/ride-rider-loop-1/ledger-receipt")

    assert rider_receipt.status_code == 200
    assert rider_replay.status_code == 200
    assert rider_ledger_receipt.status_code == 200

    ledger_payload = rider_ledger_receipt.json()
    assert ledger_payload["verdict"] == "VALID"
    assert ledger_payload["ledger_proof"]["hash_mode"] == "sha256_canonical_chain"
    assert ledger_payload["signature_validation"]["all_signatures_valid"] is True
    assert ledger_payload["identity_validation"]["all_verified"] is True
    assert ledger_payload["replay_proof"]["replay_valid"] is True


def test_driver_app_backend_contract_rejects_receipt_before_completion() -> None:
    reset_gateway()
    client = TestClient(app)

    client.post(
        "/driver/status",
        json={"driver_id": "driver-1", "online": True},
        headers={"Idempotency-Key": "driver-contract-online-reject"},
    )
    client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-contract-unfinished",
        },
        headers={"Idempotency-Key": "driver-contract-request-reject"},
    )

    receipt = client.get("/ride/ride-contract-unfinished/receipt")

    assert receipt.status_code == 400
    assert receipt.json()["error"]["code"] == "RIDE_NOT_COMPLETED"

    ledger_receipt = client.get("/ride/ride-contract-unfinished/ledger-receipt")

    assert ledger_receipt.status_code == 400
    assert ledger_receipt.json()["error"]["code"] == "RIDE_NOT_COMPLETED"
