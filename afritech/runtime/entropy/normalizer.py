"""Deterministic normalization for entropy-bound execution inputs."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


AUTHORITY_FIELDS = frozenset(
    {
        "admissibility_truth",
        "authoritative_identity",
        "canonical_replay_hash",
        "final_authority",
        "identity_truth",
        "replay_truth",
        "system_truth",
    }
)


class EntropyNormalizationError(ValueError):
    """Raised when a raw entropy event cannot be normalized safely."""


@dataclass(frozen=True)
class NormalizedEntropyEvent:
    canonical_id: str
    event_id: str
    identity_id: str
    sequence: int
    source: str
    normalized_timestamp: str
    received_order: int
    partition_id: str
    payload: Mapping[str, Any]
    raw_event_hash: str
    canonical_event_hash: str
    corrupted: bool = False
    corruption_reason: str = ""

    def canonical_dict(self) -> dict[str, object]:
        return {
            "canonical_event_hash": self.canonical_event_hash,
            "canonical_id": self.canonical_id,
            "corrupted": self.corrupted,
            "corruption_reason": self.corruption_reason,
            "event_id": self.event_id,
            "identity_id": self.identity_id,
            "normalized_timestamp": self.normalized_timestamp,
            "partition_id": self.partition_id,
            "payload": _canonicalize(self.payload),
            "raw_event_hash": self.raw_event_hash,
            "received_order": self.received_order,
            "sequence": self.sequence,
            "source": self.source,
        }


def normalize(raw_event: Mapping[str, Any]) -> NormalizedEntropyEvent:
    if not isinstance(raw_event, Mapping):
        raise EntropyNormalizationError("raw entropy event must be a mapping")

    raw_hash = _canonical_hash(raw_event)
    event_id = _text(raw_event.get("event_id"), "event_id")
    identity_id = _text(raw_event.get("identity_id"), "identity_id")
    sequence = _non_negative_int(raw_event.get("sequence"), "sequence")
    received_order = _non_negative_int(
        raw_event.get("received_order", sequence),
        "received_order",
    )
    source = _text(raw_event.get("source", "unknown"), "source")
    partition_id = _text(raw_event.get("partition_id", "partition.default"), "partition_id")
    normalized_timestamp = _normalize_time(raw_event.get("source_timestamp"))
    payload = raw_event.get("payload", {})

    corrupted = bool(raw_event.get("corrupted", False))
    corruption_reason = ""
    sanitized_payload: Mapping[str, Any]
    if not isinstance(payload, Mapping):
        corrupted = True
        corruption_reason = "payload_not_mapping"
        sanitized_payload = {"isolated_payload_hash": _canonical_hash(payload)}
    else:
        forbidden = sorted(AUTHORITY_FIELDS & set(payload))
        if forbidden:
            corrupted = True
            corruption_reason = f"authority_fields:{','.join(forbidden)}"
        sanitized_payload = _sanitize_payload(payload)

    canonical_basis = {
        "event_id": event_id,
        "identity_id": identity_id,
        "payload": _canonicalize(sanitized_payload),
        "sequence": sequence,
    }
    canonical_id = _canonical_hash(canonical_basis)
    canonical_event_hash = _canonical_hash(
        {
            "canonical_id": canonical_id,
            "event_id": event_id,
            "identity_id": identity_id,
            "payload": _canonicalize(sanitized_payload),
            "sequence": sequence,
        }
    )

    return NormalizedEntropyEvent(
        canonical_event_hash=canonical_event_hash,
        canonical_id=canonical_id,
        corrupted=corrupted,
        corruption_reason=corruption_reason,
        event_id=event_id,
        identity_id=identity_id,
        normalized_timestamp=normalized_timestamp,
        partition_id=partition_id,
        payload=sanitized_payload,
        raw_event_hash=raw_hash,
        received_order=received_order,
        sequence=sequence,
        source=source,
    )


def _sanitize_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        str(key): _canonicalize(value)
        for key, value in sorted(payload.items(), key=lambda item: str(item[0]))
        if str(key) not in AUTHORITY_FIELDS
    }


def _normalize_time(value: Any) -> str:
    if value is None:
        return "observed-time-not-authoritative"
    return str(value).strip() or "observed-time-not-authoritative"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EntropyNormalizationError(f"{field} must be non-empty text")
    return value.strip()


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EntropyNormalizationError(f"{field} must be a non-negative int")
    return value


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
