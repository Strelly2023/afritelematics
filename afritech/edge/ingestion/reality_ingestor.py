"""Admission and ingestion for normalized reality events."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from afritech.edge.ingestion.queue_ingestor import PublishQueue
from afritech.edge.normalization.reality_events import stable_hash


REQUIRED_REALITY_SCHEMA = "afritech.edge.normalization.reality_event.v1"
REQUIRED_PRE_INGESTION_STAGES = ("adapter", "normalization")
REQUIRED_ADMITTED_STAGES = ("adapter", "normalization", "ingestion")


def admit_normalized_reality_events(
    events: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Validate normalized events and stamp the ingestion trace stage."""

    admitted: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for expected_index, event in enumerate(events):
        validate_normalized_reality_event(event, expected_index=expected_index)
        normalized_event_id = str(event["normalized_event_id"])
        if normalized_event_id in seen_ids:
            raise ValueError("Duplicate normalized_event_id in admission batch")
        seen_ids.add(normalized_event_id)

        admitted_event = deepcopy(dict(event))
        admitted_event["trace"] = {
            **dict(admitted_event["trace"]),
            "stages": list(REQUIRED_ADMITTED_STAGES),
            "admission_status": "admitted_normalized_reality_event",
        }
        admitted.append(admitted_event)

    return tuple(admitted)


def ingest_normalized_reality_events(
    events: Sequence[Mapping[str, Any]],
    queue: PublishQueue,
    *,
    partition_id: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """Admit and enqueue normalized reality events through a declared queue."""

    admitted = admit_normalized_reality_events(events)
    for event in admitted:
        if partition_id is None:
            queue.publish(event)
        else:
            queue.publish(event, partition_id)
    return admitted


def validate_normalized_reality_event(
    event: Mapping[str, Any],
    *,
    expected_index: int | None = None,
) -> None:
    """Fail closed unless an event matches the ADR-302 normalized shape."""

    if event.get("schema") != REQUIRED_REALITY_SCHEMA:
        raise ValueError("Normalized reality event schema mismatch")
    if not isinstance(event.get("source_adapter_version"), str) or not event.get(
        "source_adapter_version"
    ):
        raise ValueError("Normalized reality event requires source adapter version")
    for key in ("source_id", "external_event_id", "event_kind"):
        if not isinstance(event.get(key), str) or not event.get(key):
            raise ValueError(f"Normalized reality event requires {key}")
    for key in ("authority_time_bucket", "observed_time_bucket", "sequence_index"):
        if not isinstance(event.get(key), int):
            raise ValueError(f"Normalized reality event requires integer {key}")
    if expected_index is not None and event["sequence_index"] != expected_index:
        raise ValueError("Normalized reality event sequence is not contiguous")

    _validate_sha256(event.get("payload_hash"), "payload_hash")
    _validate_sha256(event.get("normalized_event_id"), "normalized_event_id")

    trace = event.get("trace")
    if not isinstance(trace, Mapping):
        raise ValueError("Normalized reality event requires trace")
    stages = trace.get("stages")
    if tuple(stages or ()) != REQUIRED_PRE_INGESTION_STAGES:
        raise ValueError("Normalized reality event must be pre-ingestion")
    if trace.get("ordering_authority") != "received_at_ms":
        raise ValueError("Normalized reality event ordering authority mismatch")
    if trace.get("client_clock_authority") != "observational_only":
        raise ValueError("Normalized reality event client clock authority mismatch")

    expected_id = stable_hash(
        {
            "authority_time_bucket": event["authority_time_bucket"],
            "event_kind": event["event_kind"],
            "external_event_id": event["external_event_id"],
            "payload_hash": event["payload_hash"],
            "sequence_index": event["sequence_index"],
            "source_id": event["source_id"],
            "source_adapter_version": event["source_adapter_version"],
        }
    )
    if event["normalized_event_id"] != expected_id:
        raise ValueError("Normalized reality event id does not match content")

    gps_cell = event.get("gps_cell")
    if gps_cell is not None:
        _validate_gps_cell(gps_cell)


def _validate_sha256(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"Normalized reality event requires SHA-256 {field_name}")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"Normalized reality event requires hex {field_name}")


def _validate_gps_cell(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("Normalized reality event gps_cell must be a mapping")
    for key in ("lat_e", "lon_e", "precision"):
        if not isinstance(value.get(key), int):
            raise ValueError(f"Normalized reality event gps_cell requires {key}")
