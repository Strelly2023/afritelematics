"""Deterministic normalization for noisy real-world edge observations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "replay_hash",
        "replay_id",
        "witness_hash",
        "mutation_witness",
        "constitutional_authority",
    }
)


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible values in a replay-stable form."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    """Hash a canonical JSON value with SHA-256."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_reality_events(
    observations: Iterable[Mapping[str, Any]],
    *,
    source_adapter_version: str,
    timestamp_bucket_ms: int = 1000,
    coordinate_precision: int = 5,
) -> tuple[dict[str, Any], ...]:
    """Collapse unordered raw observations into deterministic edge events.

    The input order is intentionally ignored. Each observation must carry an
    ingress-controlled ``received_at_ms`` timestamp; device/client time is
    preserved only as observational evidence and never used as ordering
    authority.
    """

    if timestamp_bucket_ms <= 0:
        raise ValueError("timestamp_bucket_ms must be positive")
    if coordinate_precision < 0:
        raise ValueError("coordinate_precision must be non-negative")
    if not source_adapter_version:
        raise ValueError("source_adapter_version must be non-empty")

    deduped: dict[tuple[str, str], dict[str, Any]] = {}

    for observation in observations:
        normalized = normalize_reality_event(
            observation,
            source_adapter_version=source_adapter_version,
            timestamp_bucket_ms=timestamp_bucket_ms,
            coordinate_precision=coordinate_precision,
        )
        dedupe_key = (
            normalized["source_id"],
            normalized["external_event_id"],
        )
        previous = deduped.get(dedupe_key)
        if previous is None:
            deduped[dedupe_key] = normalized
            continue

        if _duplicate_signature(previous) != _duplicate_signature(normalized):
            raise ValueError("Conflicting duplicate external event")

    ordered = sorted(
        deduped.values(),
        key=lambda event: (
            event["authority_time_bucket"],
            event["source_id"],
            event["external_event_id"],
            event["event_kind"],
            event["payload_hash"],
        ),
    )

    return tuple(
        {
            **event,
            "sequence_index": index,
            "normalized_event_id": stable_hash(
                {
                    "authority_time_bucket": event["authority_time_bucket"],
                    "event_kind": event["event_kind"],
                    "external_event_id": event["external_event_id"],
                    "payload_hash": event["payload_hash"],
                    "sequence_index": index,
                    "source_id": event["source_id"],
                    "source_adapter_version": event["source_adapter_version"],
                }
            ),
        }
        for index, event in enumerate(ordered)
    )


def normalize_reality_event(
    observation: Mapping[str, Any],
    *,
    source_adapter_version: str,
    timestamp_bucket_ms: int = 1000,
    coordinate_precision: int = 5,
) -> dict[str, Any]:
    """Normalize one raw observation without relying on process state."""

    if not source_adapter_version:
        raise ValueError("source_adapter_version must be non-empty")

    _reject_authority_injection(observation)

    payload = observation.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("Reality observation payload must be a mapping")
    _reject_authority_injection(payload)

    received_at_ms = int(observation["received_at_ms"])
    observed_at_ms = int(observation.get("observed_at_ms", received_at_ms))
    event_kind = str(observation.get("event_kind", "external_observation"))
    source_id = str(observation["source_id"])
    external_event_id = str(observation["event_id"])

    normalized: dict[str, Any] = {
        "schema": "afritech.edge.normalization.reality_event.v1",
        "source_adapter_version": str(source_adapter_version),
        "source_id": source_id,
        "external_event_id": external_event_id,
        "event_kind": event_kind,
        "authority_time_bucket": received_at_ms // timestamp_bucket_ms,
        "observed_time_bucket": observed_at_ms // timestamp_bucket_ms,
        "payload_hash": stable_hash(dict(payload)),
        "trace": {
            "stages": ["adapter", "normalization"],
            "ordering_authority": "received_at_ms",
            "client_clock_authority": "observational_only",
        },
    }

    gps_cell = _normalize_gps_cell(
        payload,
        coordinate_precision=coordinate_precision,
    )
    if gps_cell is not None:
        normalized["gps_cell"] = gps_cell

    for routing_key in ("city_id", "trip_id", "device_id", "user_id"):
        value = payload.get(routing_key)
        if value is not None:
            normalized[routing_key] = str(value)

    return normalized


def _duplicate_signature(event: Mapping[str, Any]) -> dict[str, Any]:
    signature = deepcopy(dict(event))
    signature.pop("sequence_index", None)
    signature.pop("normalized_event_id", None)
    return signature


def _reject_authority_injection(value: Mapping[str, Any]) -> None:
    injected = FORBIDDEN_AUTHORITY_FIELDS.intersection(value.keys())
    if injected:
        field = sorted(injected)[0]
        raise ValueError(f"Forbidden authority field in edge input: {field}")

    for nested in value.values():
        if isinstance(nested, Mapping):
            _reject_authority_injection(nested)
        elif isinstance(nested, list):
            for item in nested:
                if isinstance(item, Mapping):
                    _reject_authority_injection(item)


def _normalize_gps_cell(
    payload: Mapping[str, Any],
    *,
    coordinate_precision: int,
) -> dict[str, int] | None:
    latitude = payload.get("latitude", payload.get("lat"))
    longitude = payload.get("longitude", payload.get("lon"))
    if latitude is None and longitude is None:
        return None
    if latitude is None or longitude is None:
        raise ValueError("GPS observation requires both latitude and longitude")

    lat = Decimal(str(latitude))
    lon = Decimal(str(longitude))
    if lat < Decimal("-90") or lat > Decimal("90"):
        raise ValueError("GPS latitude out of range")
    if lon < Decimal("-180") or lon > Decimal("180"):
        raise ValueError("GPS longitude out of range")

    scale = Decimal(10) ** coordinate_precision
    return {
        "lat_e": _quantize_coordinate(lat, scale),
        "lon_e": _quantize_coordinate(lon, scale),
        "precision": coordinate_precision,
    }


def _quantize_coordinate(value: Decimal, scale: Decimal) -> int:
    return int((value * scale).to_integral_value(rounding=ROUND_HALF_UP))
