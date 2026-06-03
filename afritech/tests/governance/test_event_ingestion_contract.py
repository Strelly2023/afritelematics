from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.ingestion.event_ingestion import (
    EventIngestionAPI,
    MobileEventAuthenticator,
)


SECRET = "pilot-secret"


def make_valid_event(
    *,
    event_id: str = "evt-001",
    event_type: str = "TRIP_STARTED",
    device_id: str = "driver-1",
    entity_id: str = "ride-1",
    timestamp: int = 1_700_000_001_000,
    logical_clock: int = 1,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "device_id": device_id,
        "entity_id": entity_id,
        "timestamp": timestamp,
        "logical_clock": logical_clock,
        "payload": payload if payload is not None else {"ride_id": entity_id},
        "signature": "0" * 64,
    }
    event["signature"] = MobileEventAuthenticator().generate_signature(event, SECRET)
    return event


def test_event_schema_fields() -> None:
    required = [
        "event_id",
        "event_type",
        "device_id",
        "entity_id",
        "timestamp",
        "logical_clock",
        "payload",
        "signature",
    ]

    event = make_valid_event()

    for field in required:
        assert field in event


def test_event_rejection_on_bad_signature() -> None:
    api = EventIngestionAPI(SECRET)
    event = make_valid_event()
    event["signature"] = "f" * 64

    result = api.ingest([event], received_at_ms=1_700_000_002_000)

    assert result["accepted"] == []
    assert result["rejected"] == [
        {"event_id": "evt-001", "reason": "invalid_signature"}
    ]


def test_event_rejection_on_missing_required_field() -> None:
    api = EventIngestionAPI(SECRET)
    event = make_valid_event()
    del event["logical_clock"]

    result = api.ingest([event], received_at_ms=1_700_000_002_000)

    assert result["accepted"] == []
    assert result["rejected"] == [
        {"event_id": "evt-001", "reason": "invalid_structure"}
    ]


def test_duplicate_event_id_is_rejected_deterministically() -> None:
    api = EventIngestionAPI(SECRET)
    event = make_valid_event()

    first = api.ingest([event], received_at_ms=1_700_000_002_000)
    second = api.ingest([event], received_at_ms=1_700_000_003_000)

    assert first["accepted"] == ["evt-001"]
    assert second["accepted"] == []
    assert second["rejected"] == [
        {"event_id": "evt-001", "reason": "duplicate_event"}
    ]


def test_logical_clock_regression_is_rejected_per_device() -> None:
    api = EventIngestionAPI(SECRET)
    first = make_valid_event(event_id="evt-002", logical_clock=2)
    regressed = make_valid_event(event_id="evt-001", logical_clock=1)

    api.ingest([first], received_at_ms=1_700_000_002_000)
    result = api.ingest([regressed], received_at_ms=1_700_000_003_000)

    assert result["accepted"] == []
    assert result["rejected"] == [
        {"event_id": "evt-001", "reason": "logical_clock_regression"}
    ]


def test_forbidden_authority_field_is_rejected_before_normalization() -> None:
    api = EventIngestionAPI(SECRET)
    event = make_valid_event(payload={"ride_id": "ride-1", "replay_hash": "forged"})

    result = api.ingest([event], received_at_ms=1_700_000_002_000)

    assert result["accepted"] == []
    assert result["rejected"] == [
        {"event_id": "evt-001", "reason": "forbidden_authority_field"}
    ]


def test_accepted_events_are_forwarded_to_normalization_pipeline() -> None:
    api = EventIngestionAPI(SECRET)
    event = make_valid_event(
        event_type="DRIVER_LOCATION_UPDATE",
        payload={
            "ride_id": "ride-1",
            "latitude": "-37.813628",
            "longitude": "144.963058",
        },
    )

    result = api.ingest([event], received_at_ms=1_700_000_002_000)

    assert result["accepted"] == ["evt-001"]
    assert result["rejected"] == []
    normalized = result["normalized_events"][0]
    assert normalized["external_event_id"] == "evt-001"
    assert normalized["source_id"] == "driver-1"
    assert normalized["event_kind"] == "DRIVER_LOCATION_UPDATE"
    assert normalized["trace"]["stages"] == ["adapter", "normalization"]
    assert normalized["gps_cell"] == {
        "lat_e": -3781363,
        "lon_e": 14496306,
        "precision": 5,
    }


def test_fastapi_v1_events_endpoint_returns_contract_response() -> None:
    client = TestClient(app)
    event = make_valid_event(event_id="evt-fastapi-001")

    response = client.post(
        "/v1/events",
        json={"events": [event], "received_at_ms": 1_700_000_002_000},
    )

    assert response.status_code == 200
    assert response.json() == {"accepted": ["evt-fastapi-001"], "rejected": []}
