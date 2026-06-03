from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app
from afriride_system.backend.event_ledger import (
    EventLedgerHasher,
    EventLedgerValidationError,
    EventLedgerValidator,
)
from afriride_system.backend.ledger_receipts import (
    LedgerReceiptError,
    LedgerReceiptGenerator,
    LedgerReceiptValidator,
)
from afriride_system.tests.test_ledger_receipts import _signed_events


def test_duplicate_driver_acceptance_fails_closed() -> None:
    client = _prepared_client("ride-duplicate-accept")
    accepted = client.post(
        "/ride/ride-duplicate-accept/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "accept-driver-1"},
    )
    duplicate = client.post(
        "/ride/ride-duplicate-accept/accept",
        json={"driver_id": "driver-2"},
        headers={"Idempotency-Key": "accept-driver-2"},
    )
    status = client.get("/passenger/status/ride-duplicate-accept")

    assert accepted.status_code == 200
    assert duplicate.status_code == 400
    assert duplicate.json()["error"]["code"] == "RIDE_NOT_ACCEPTING_DRIVER"
    assert status.json()["data"]["assigned_driver"] == "driver-1"
    assert status.json()["data"]["events"].count("driver_assigned") == 1


def test_matching_is_deterministic_for_identical_inputs() -> None:
    first = _assignment_result_for_request("ride-deterministic-1")
    second = _assignment_result_for_request("ride-deterministic-2")

    assert first["assigned_driver"] == "driver-1"
    assert second["assigned_driver"] == first["assigned_driver"]
    assert second["trace_hash"] == first["trace_hash"]
    assert second["state_hash"] == first["state_hash"]


def test_driver_mismatch_fails_closed() -> None:
    client = _prepared_client("ride-driver-mismatch")
    client.post(
        "/ride/ride-driver-mismatch/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "mismatch-accept"},
    )

    start = client.post(
        "/ride/ride-driver-mismatch/start",
        json={"driver_id": "driver-2"},
        headers={"Idempotency-Key": "mismatch-start"},
    )

    assert start.status_code == 400
    assert start.json()["error"]["code"] == "DRIVER_NOT_ASSIGNED_TO_RIDE"


def test_cross_app_lifecycle_drift_fails_closed_after_completion() -> None:
    client = _completed_client("ride-lifecycle-drift")
    start_again = client.post(
        "/ride/ride-lifecycle-drift/start",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "drift-start-after-complete"},
    )

    assert start_again.status_code == 400
    assert start_again.json()["error"]["code"] == "TRIP_NOT_READY_TO_START"


def test_double_completion_fails_closed() -> None:
    client = _completed_client("ride-double-complete")
    complete_again = client.post(
        "/ride/ride-double-complete/complete",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": "double-complete"},
    )

    assert complete_again.status_code == 400
    assert complete_again.json()["error"]["code"] == "TRIP_NOT_IN_PROGRESS"


def test_tampered_receipt_is_rejected_and_ledger_remains_source_of_truth() -> None:
    events, signature_validator = _signed_events()
    receipt = LedgerReceiptGenerator(
        validator=EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        )
    ).generate(
        events,
        receipt_id="rcpt_tamper_check",
        event_log_id="log_tamper_check",
        replay_run_id="replay_tamper_check",
        generated_at="2026-06-01T14:00:00Z",
    )
    tampered = deepcopy(receipt.canonical_dict())
    tampered["financial_summary"]["total_fare"] = 999

    with pytest.raises(LedgerReceiptError, match="receipt hash mismatch"):
        LedgerReceiptValidator().validate(tampered)

    original = LedgerReceiptValidator().validate(receipt)
    assert original["valid"] is True


def test_replay_divergence_in_event_chain_fails_closed() -> None:
    events, _ = _signed_events()
    unsigned_events = [
        {
            key: value
            for key, value in event.items()
            if key
            not in {
                "signer_id",
                "public_key_id",
                "device_id",
                "terms_version",
                "signature",
            }
        }
        for event in events
    ]
    diverged = deepcopy(unsigned_events)
    diverged[19]["distance_km"] = 999

    with pytest.raises(EventLedgerValidationError, match="cryptographic hash mismatch"):
        EventLedgerValidator(require_cryptographic_hashes=True).validate(diverged)


def test_out_of_order_lifecycle_event_chain_fails_closed() -> None:
    events = EventLedgerHasher().materialize_sha256_chain(
        [
            {
                "event_id": "evt-1",
                "type": "DRIVER_ONLINE",
                "driver_id": "driver-1",
                "timestamp": "2026-06-01T00:00:00Z",
            },
            {
                "event_id": "evt-2",
                "type": "RIDE_STARTED",
                "ride_id": "ride-out-of-order",
                "timestamp": "2026-06-01T00:01:00Z",
            },
            {
                "event_id": "evt-3",
                "type": "RIDE_REQUEST_CREATED",
                "ride_id": "ride-out-of-order",
                "rider_id": "rider-1",
                "timestamp": "2026-06-01T00:02:00Z",
            },
        ]
    )

    with pytest.raises(EventLedgerValidationError, match="invalid lifecycle sequence"):
        EventLedgerValidator(require_cryptographic_hashes=True).validate(events)


def _prepared_client(ride_id: str) -> TestClient:
    reset_gateway()
    client = TestClient(app)
    for driver_id in ("driver-1", "driver-2"):
        client.post(
            "/driver/status",
            json={"driver_id": driver_id, "online": True},
            headers={"Idempotency-Key": f"{ride_id}-{driver_id}-online"},
        )
    client.post(
        "/passenger/request-ride",
        json={
            "passenger_id": "rider-1",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": ride_id,
        },
        headers={"Idempotency-Key": f"{ride_id}-request"},
    )
    return client


def _completed_client(ride_id: str) -> TestClient:
    client = _prepared_client(ride_id)
    client.post(
        f"/ride/{ride_id}/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": f"{ride_id}-accept"},
    )
    client.post(
        f"/ride/{ride_id}/start",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": f"{ride_id}-start"},
    )
    client.post(
        f"/ride/{ride_id}/complete",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": f"{ride_id}-complete"},
    )
    return client


def _assignment_result_for_request(ride_id: str) -> dict:
    client = _prepared_client(ride_id)
    response = client.post(
        f"/ride/{ride_id}/accept",
        json={"driver_id": "driver-1"},
        headers={"Idempotency-Key": f"{ride_id}-deterministic-accept"},
    )
    assert response.status_code == 200
    return response.json()
