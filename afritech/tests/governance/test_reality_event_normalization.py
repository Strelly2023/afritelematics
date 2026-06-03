from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from afritech.edge.ingestion.reality_ingestor import (
    admit_normalized_reality_events,
    ingest_normalized_reality_events,
)
from afritech.edge.normalization.reality_events import normalize_reality_events


@dataclass
class MemoryQueue:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, event: dict[str, Any], partition_id: int | None = None) -> None:
        queued = dict(event)
        if partition_id is not None:
            queued["partition_id"] = partition_id
        self.events.append(queued)


def test_reality_events_converge_despite_reordering_and_duplicates() -> None:
    events = [
        {
            "source_id": "device-a",
            "event_id": "evt-002",
            "event_kind": "driver_location",
            "observed_at_ms": 1_700_000_900_999,
            "received_at_ms": 1_700_000_002_111,
            "payload": {
                "trip_id": "trip-1",
                "latitude": "-37.813628",
                "longitude": "144.963058",
            },
        },
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "event_kind": "ride_request",
            "observed_at_ms": 1_699_999_999_999,
            "received_at_ms": 1_700_000_001_999,
            "payload": {"city_id": "melbourne", "destination": "airport"},
        },
        {
            "source_id": "device-a",
            "event_id": "evt-002",
            "event_kind": "driver_location",
            "observed_at_ms": 1_700_000_900_999,
            "received_at_ms": 1_700_000_002_111,
            "payload": {
                "longitude": "144.963058",
                "latitude": "-37.813628",
                "trip_id": "trip-1",
            },
        },
    ]

    trace_a = normalize_reality_events(
        events,
        source_adapter_version="mobile-gps-v1",
    )
    trace_b = normalize_reality_events(
        reversed(events),
        source_adapter_version="mobile-gps-v1",
    )

    assert trace_a == trace_b
    assert len(trace_a) == 2
    assert [event["external_event_id"] for event in trace_a] == ["evt-001", "evt-002"]
    assert [event["sequence_index"] for event in trace_a] == [0, 1]
    assert trace_a[1]["gps_cell"] == {
        "lat_e": -3781363,
        "lon_e": 14496306,
        "precision": 5,
    }
    assert trace_a[0]["trace"]["ordering_authority"] == "received_at_ms"
    assert trace_a[0]["trace"]["client_clock_authority"] == "observational_only"


def test_normalized_reality_events_require_admission_before_ingestion() -> None:
    normalized = normalize_reality_events(
        [
            {
                "source_id": "device-a",
                "event_id": "evt-001",
                "event_kind": "ride_request",
                "received_at_ms": 1_700_000_001_999,
                "payload": {"city_id": "melbourne", "destination": "airport"},
            }
        ],
        source_adapter_version="mobile-v1",
    )
    queue = MemoryQueue()

    admitted = ingest_normalized_reality_events(normalized, queue, partition_id=3)

    assert admitted[0]["trace"]["stages"] == [
        "adapter",
        "normalization",
        "ingestion",
    ]
    assert admitted[0]["trace"]["admission_status"] == (
        "admitted_normalized_reality_event"
    )
    assert queue.events[0]["normalized_event_id"] == admitted[0]["normalized_event_id"]
    assert queue.events[0]["partition_id"] == 3


def test_admission_rejects_tampered_normalized_event_id() -> None:
    normalized = list(
        normalize_reality_events(
            [
                {
                    "source_id": "device-a",
                    "event_id": "evt-001",
                    "received_at_ms": 1_700_000_001_000,
                    "payload": {"destination": "airport"},
                }
            ],
            source_adapter_version="mobile-v1",
        )
    )
    normalized[0] = {**normalized[0], "normalized_event_id": "0" * 64}

    with pytest.raises(ValueError, match="id does not match content"):
        admit_normalized_reality_events(normalized)


def test_admission_rejects_sequence_gaps() -> None:
    normalized = list(
        normalize_reality_events(
            [
                {
                    "source_id": "device-a",
                    "event_id": "evt-001",
                    "received_at_ms": 1_700_000_001_000,
                    "payload": {"destination": "airport"},
                }
            ],
            source_adapter_version="mobile-v1",
        )
    )
    normalized[0] = {**normalized[0], "sequence_index": 2}

    with pytest.raises(ValueError, match="sequence is not contiguous"):
        admit_normalized_reality_events(normalized)


def test_conflicting_duplicate_reality_event_is_rejected() -> None:
    events = [
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "received_at_ms": 1_700_000_001_000,
            "payload": {"destination": "airport"},
        },
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "received_at_ms": 1_700_000_001_000,
            "payload": {"destination": "cbd"},
        },
    ]

    with pytest.raises(ValueError, match="Conflicting duplicate"):
        normalize_reality_events(events, source_adapter_version="mobile-v1")


def test_replay_authority_injection_is_rejected_at_normalization_boundary() -> None:
    events = [
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "received_at_ms": 1_700_000_001_000,
            "payload": {
                "destination": "airport",
                "replay_hash": "attacker-controlled",
            },
        },
    ]

    with pytest.raises(ValueError, match="Forbidden authority field"):
        normalize_reality_events(events, source_adapter_version="mobile-v1")


def test_nested_replay_authority_injection_is_rejected() -> None:
    events = [
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "received_at_ms": 1_700_000_001_000,
            "payload": {
                "destination": "airport",
                "metadata": {"witness_hash": "attacker-controlled"},
            },
        },
    ]

    with pytest.raises(ValueError, match="Forbidden authority field"):
        normalize_reality_events(events, source_adapter_version="mobile-v1")


def test_invalid_gps_observation_is_rejected_before_admission() -> None:
    events = [
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "received_at_ms": 1_700_000_001_000,
            "payload": {"latitude": "91", "longitude": "144.9631"},
        },
    ]

    with pytest.raises(ValueError, match="GPS latitude out of range"):
        normalize_reality_events(events, source_adapter_version="mobile-gps-v1")
