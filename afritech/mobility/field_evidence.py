"""Deterministic field evidence collection for Gen-3 mobility operations.

ADR-0042 captures real-world events as replayable evidence without granting
truth authority to the evidence surface itself.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ecosystems.afriride.geo.types import GeoPoint

from .trust_dispatch import DispatchDecision, DispatchDecisionError


SCHEMA = "afritech.mobility.field_evidence.v1"
AUTHORITY_BOUNDARY = "field_evidence_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "field_evidence_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "field_evidence_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "field_evidence_proof_read_only"

CANONICAL_FIELD_EVENT_TYPES = (
    "GPS",
    "DRIVER_ACCEPT",
    "ARRIVAL",
    "PICKUP",
    "DROPOFF",
    "CUSTOMER_CONFIRM",
    "PAYMENT_CONFIRM",
)

FIELD_EVIDENCE_SIGNAL_SCHEMA = "afritech.mobility.field_evidence_signal.v1"
FIELD_EVIDENCE_INGESTION_SCHEMA = "afritech.mobility.field_evidence_ingestion.v1"
INGESTION_AUTHORITY_BOUNDARY = "field_evidence_ingestion_read_only"

FORBIDDEN_SIGNAL_AUTHORITY_FIELDS = frozenset(
    {
        "authority",
        "canonical_truth",
        "constitutional_authority",
        "dispatch_override",
        "proof_hash",
        "replay_hash",
        "replay_id",
        "settlement_authority",
        "truth",
        "witness_hash",
    }
)

MAX_GPS_JUMP_KM = 250.0
MAX_GPS_JUMP_SECONDS = 3600

INVARIANT_IDS = (
    "IA-FIELD-001",
    "IA-FIELD-002",
    "IA-FIELD-003",
    "IA-FIELD-004",
    "IA-FIELD-005",
    "IA-FIELD-006",
)


class FieldEvidenceError(ValueError):
    """Raised when field evidence payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FieldEvidenceError(f"{label} is required")
    return value.strip()


def _require_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise FieldEvidenceError(f"{label} must be an integer")
    return value


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise FieldEvidenceError("payload must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _reject_signal_authority_fields(value: Mapping[str, Any], *, path: str = "signal") -> None:
    injected = FORBIDDEN_SIGNAL_AUTHORITY_FIELDS.intersection(value.keys())
    if injected:
        field_name = sorted(injected)[0]
        raise FieldEvidenceError(f"forbidden authority field in {path}: {field_name}")
    for key, nested in value.items():
        if isinstance(nested, Mapping):
            _reject_signal_authority_fields(nested, path=f"{path}.{key}")


def _geo_from_value(value: GeoPoint | Mapping[str, Any]) -> GeoPoint:
    if isinstance(value, GeoPoint):
        return value
    if not isinstance(value, Mapping):
        raise FieldEvidenceError("location must be a mapping or GeoPoint")
    try:
        lat = float(value["lat"])
        lon = float(value["lon"])
        timestamp = int(value["timestamp"])
    except KeyError as exc:  # pragma: no cover - defensive
        raise FieldEvidenceError(f"missing location field: {exc.args[0]}") from exc
    if not -90.0 <= lat <= 90.0:
        raise FieldEvidenceError("latitude must be between -90 and 90")
    if not -180.0 <= lon <= 180.0:
        raise FieldEvidenceError("longitude must be between -180 and 180")
    return GeoPoint(lat=lat, lon=lon, timestamp=timestamp)


def _haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    from math import asin, cos, radians, sin, sqrt

    lat1 = radians(a.lat)
    lat2 = radians(b.lat)
    dlat = lat2 - lat1
    dlon = radians(b.lon - a.lon)
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(hav))


def _normalize_event_type(value: object) -> str:
    event_type = _require_text(value, "event_type")
    if event_type not in CANONICAL_FIELD_EVENT_TYPES:
        raise FieldEvidenceError("unsupported field event type")
    return event_type


def _normalize_events(values: Iterable[object]) -> tuple["FieldEvent", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise FieldEvidenceError("field_events must be iterable")
    events = tuple(item if isinstance(item, FieldEvent) else FieldEvent.from_mapping(item) for item in values)
    return tuple(sorted(events, key=lambda event: (event.timestamp, event.event_id)))


def _dispatch_binding(dispatch: DispatchDecision | Mapping[str, Any] | None) -> tuple[str, str, str] | None:
    if dispatch is None:
        return None
    normalized = dispatch if isinstance(dispatch, DispatchDecision) else DispatchDecision.from_mapping(dispatch)
    return normalized.request.operation_id, normalized.selected_participant_id, normalized.decision_hash


@dataclass(frozen=True)
class FieldEvent:
    event_id: str
    operation_id: str
    participant_id: str
    event_type: str
    timestamp: int
    location: GeoPoint
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    evidence_hash: str = ""
    authority_boundary: str = AUTHORITY_BOUNDARY
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "event_type", _normalize_event_type(self.event_type))
        object.__setattr__(self, "timestamp", _require_int(self.timestamp, "timestamp"))
        object.__setattr__(self, "location", _geo_from_value(self.location))
        object.__setattr__(self, "payload", _freeze_mapping(dict(self.payload)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise FieldEvidenceError("field event authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise FieldEvidenceError("field events must be verified")
        payload = self._hash_payload()
        if self.evidence_hash:
            if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
                raise FieldEvidenceError("evidence_hash must be a 64-character hex digest")
            if self.evidence_hash != _canonical_hash(payload):
                raise FieldEvidenceError("evidence_hash mismatch")
        else:
            object.__setattr__(self, "evidence_hash", _canonical_hash(payload))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FieldEvent":
        if not isinstance(payload, Mapping):
            raise FieldEvidenceError("field event payload must be a mapping")
        return cls(
            event_id=_require_text(payload.get("event_id") or payload.get("id"), "event_id"),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            event_type=_normalize_event_type(payload.get("event_type")),
            timestamp=int(payload.get("timestamp", 0)),
            location=_geo_from_value(payload.get("location", {})),
            payload=_freeze_mapping(payload.get("payload", {})),
            evidence_hash=_require_text(payload.get("evidence_hash", ""), "evidence_hash") if payload.get("evidence_hash") else "",
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            verified=bool(payload.get("verified", True)),
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "location": self.location.canonical(),
            "operation_id": self.operation_id,
            "participant_id": self.participant_id,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["evidence_hash"] = self.evidence_hash
        payload["schema"] = SCHEMA
        return payload

    @property
    def event_hash(self) -> str:
        return self.evidence_hash


@dataclass(frozen=True)
class FieldEvidenceSignal:
    signal_id: str
    source_id: str
    source_adapter_version: str
    operation_id: str
    participant_id: str
    event_type: str
    observed_at: int
    received_at: int
    location: GeoPoint
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    signal_hash: str = ""
    schema: str = FIELD_EVIDENCE_SIGNAL_SCHEMA
    authority_boundary: str = INGESTION_AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", _require_text(self.signal_id, "signal_id"))
        object.__setattr__(self, "source_id", _require_text(self.source_id, "source_id"))
        object.__setattr__(
            self,
            "source_adapter_version",
            _require_text(self.source_adapter_version, "source_adapter_version"),
        )
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "event_type", _normalize_event_type(self.event_type))
        object.__setattr__(self, "observed_at", _require_int(self.observed_at, "observed_at"))
        object.__setattr__(self, "received_at", _require_int(self.received_at, "received_at"))
        object.__setattr__(self, "location", _geo_from_value(self.location))
        object.__setattr__(self, "payload", _freeze_mapping(dict(self.payload)))
        object.__setattr__(self, "schema", _require_text(self.schema, "schema"))
        object.__setattr__(
            self,
            "authority_boundary",
            _require_text(self.authority_boundary, "authority_boundary"),
        )
        if self.schema != FIELD_EVIDENCE_SIGNAL_SCHEMA:
            raise FieldEvidenceError("field evidence signal schema mismatch")
        if self.authority_boundary != INGESTION_AUTHORITY_BOUNDARY:
            raise FieldEvidenceError("field evidence signal authority boundary mismatch")
        if self.received_at < self.observed_at:
            raise FieldEvidenceError("received_at must not be earlier than observed_at")
        payload = self._hash_payload()
        if self.signal_hash:
            if not isinstance(self.signal_hash, str) or len(self.signal_hash) != 64:
                raise FieldEvidenceError("signal_hash must be a 64-character hex digest")
            if self.signal_hash != _canonical_hash(payload):
                raise FieldEvidenceError("signal_hash mismatch")
        else:
            object.__setattr__(self, "signal_hash", _canonical_hash(payload))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FieldEvidenceSignal":
        if not isinstance(payload, Mapping):
            raise FieldEvidenceError("field evidence signal must be a mapping")
        _reject_signal_authority_fields(payload)
        signal_payload = payload.get("payload", {})
        if not isinstance(signal_payload, Mapping):
            raise FieldEvidenceError("field evidence signal payload must be a mapping")
        _reject_signal_authority_fields(signal_payload, path="signal.payload")
        if "authority_boundary" in signal_payload:
            raise FieldEvidenceError("forbidden authority field in signal.payload: authority_boundary")
        return cls(
            signal_id=_require_text(payload.get("signal_id") or payload.get("event_id"), "signal_id"),
            source_id=_require_text(payload.get("source_id"), "source_id"),
            source_adapter_version=_require_text(
                payload.get("source_adapter_version"),
                "source_adapter_version",
            ),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            event_type=_normalize_event_type(payload.get("event_type")),
            observed_at=int(payload.get("observed_at", payload.get("timestamp", 0))),
            received_at=int(payload.get("received_at", payload.get("received_at_ms", 0))),
            location=_geo_from_value(payload.get("location", {})),
            payload=_freeze_mapping(signal_payload),
            signal_hash=_require_text(payload.get("signal_hash", ""), "signal_hash") if payload.get("signal_hash") else "",
            schema=_require_text(payload.get("schema", FIELD_EVIDENCE_SIGNAL_SCHEMA), "schema"),
            authority_boundary=_require_text(
                payload.get("authority_boundary", INGESTION_AUTHORITY_BOUNDARY),
                "authority_boundary",
            ),
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "event_type": self.event_type,
            "location": self.location.canonical(),
            "observed_at": self.observed_at,
            "operation_id": self.operation_id,
            "participant_id": self.participant_id,
            "payload": dict(self.payload),
            "received_at": self.received_at,
            "schema": self.schema,
            "signal_id": self.signal_id,
            "source_adapter_version": self.source_adapter_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["signal_hash"] = self.signal_hash
        return payload

    def to_field_event(self) -> FieldEvent:
        return FieldEvent.from_mapping(
            {
                "event_id": self.signal_id,
                "operation_id": self.operation_id,
                "participant_id": self.participant_id,
                "event_type": self.event_type,
                "timestamp": self.received_at,
                "location": {
                    "lat": self.location.lat,
                    "lon": self.location.lon,
                    "timestamp": self.received_at,
                },
                "payload": {
                    **dict(self.payload),
                    "observed_at": self.observed_at,
                    "signal_hash": self.signal_hash,
                    "source_adapter_version": self.source_adapter_version,
                    "source_id": self.source_id,
                },
            }
        )


@dataclass(frozen=True)
class FieldEvidenceCollection:
    collection_id: str
    operation_id: str
    dispatch_hash: str
    selected_participant_id: str
    field_events: tuple[FieldEvent, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY
    verified: bool = True
    collection_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "collection_id", _require_text(self.collection_id, "collection_id"))
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        object.__setattr__(self, "dispatch_hash", _require_text(self.dispatch_hash, "dispatch_hash"))
        object.__setattr__(self, "selected_participant_id", _require_text(self.selected_participant_id, "selected_participant_id"))
        if len(self.dispatch_hash) != 64:
            raise FieldEvidenceError("dispatch_hash must be a 64-character hex digest")
        object.__setattr__(self, "field_events", _normalize_events(self.field_events))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise FieldEvidenceError("field evidence authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise FieldEvidenceError("field evidence collection must be verified")
        if not self.field_events:
            raise FieldEvidenceError("field events are required")
        if tuple(event.event_type for event in self.field_events) != CANONICAL_FIELD_EVENT_TYPES:
            raise FieldEvidenceError("field event sequence mismatch")
        if any(event.operation_id != self.operation_id for event in self.field_events):
            raise FieldEvidenceError("field events must reference the collection operation_id")
        if any(event.participant_id != self.selected_participant_id for event in self.field_events):
            raise FieldEvidenceError("field events must reference the selected participant")
        payload = self._hash_payload()
        if self.collection_hash:
            if not isinstance(self.collection_hash, str) or len(self.collection_hash) != 64:
                raise FieldEvidenceError("collection_hash must be a 64-character hex digest")
            if self.collection_hash != _canonical_hash(payload):
                raise FieldEvidenceError("collection_hash mismatch")
        else:
            object.__setattr__(self, "collection_hash", _canonical_hash(payload))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FieldEvidenceCollection":
        if not isinstance(payload, Mapping):
            raise FieldEvidenceError("field evidence payload must be a mapping")
        return cls(
            collection_id=_require_text(payload.get("collection_id"), "collection_id"),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            dispatch_hash=_require_text(payload.get("dispatch_hash"), "dispatch_hash"),
            selected_participant_id=_require_text(payload.get("selected_participant_id"), "selected_participant_id"),
            field_events=tuple(payload.get("field_events", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            verified=bool(payload.get("verified", True)),
            collection_hash=_require_text(payload.get("collection_hash", ""), "collection_hash") if payload.get("collection_hash") else "",
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "collection_id": self.collection_id,
            "dispatch_hash": self.dispatch_hash,
            "field_events": [event.canonical_dict() for event in self.field_events],
            "operation_id": self.operation_id,
            "schema": SCHEMA,
            "selected_participant_id": self.selected_participant_id,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["collection_hash"] = self.collection_hash
        return payload


@dataclass(frozen=True)
class FieldEvidenceInvariantCheck:
    identifier: str
    satisfied: bool
    details: str
    evidence_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "details": self.details,
            "evidence_hash": self.evidence_hash,
            "identifier": self.identifier,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class FieldEvidenceInvariantReport:
    collection_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[FieldEvidenceInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "collection_hash": self.collection_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.field_evidence_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class FieldEvidenceValidationReport:
    collection_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "collection_hash": self.collection_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.field_evidence_validation_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class FieldEvidenceIngestionResult:
    ingestion_id: str
    source_id: str
    signal_hashes: tuple[str, ...]
    collection: FieldEvidenceCollection
    proof: Mapping[str, Any]
    invariant_report: FieldEvidenceInvariantReport
    authority_boundary: str = INGESTION_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == INGESTION_AUTHORITY_BOUNDARY
            and bool(self.signal_hashes)
            and self.collection.verified
            and self.proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY
            and self.invariant_report.verified
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "collection": self.collection.canonical_dict(),
            "collection_hash": self.collection.collection_hash,
            "ingestion_hash": self.ingestion_hash,
            "ingestion_id": self.ingestion_id,
            "invariant_report": self.invariant_report.canonical_dict(),
            "proof": dict(self.proof),
            "proof_hash": self.proof.get("proof_hash"),
            "schema": FIELD_EVIDENCE_INGESTION_SCHEMA,
            "signal_hashes": self.signal_hashes,
            "source_id": self.source_id,
            "verified": self.verified,
        }

    @property
    def ingestion_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_boundary": self.authority_boundary,
                "collection_hash": self.collection.collection_hash,
                "ingestion_id": self.ingestion_id,
                "proof_hash": self.proof.get("proof_hash"),
                "signal_hashes": self.signal_hashes,
                "source_id": self.source_id,
            }
        )


def _coerce_collection(value: FieldEvidenceCollection | Mapping[str, Any]) -> FieldEvidenceCollection:
    if isinstance(value, FieldEvidenceCollection):
        return value
    return FieldEvidenceCollection.from_mapping(value)


def _normalize_dispatch(dispatch: DispatchDecision | Mapping[str, Any] | None) -> DispatchDecision | None:
    if dispatch is None:
        return None
    try:
        return dispatch if isinstance(dispatch, DispatchDecision) else DispatchDecision.from_mapping(dispatch)
    except DispatchDecisionError as exc:
        raise FieldEvidenceError(str(exc)) from exc


def build_field_evidence_collection(
    dispatch: DispatchDecision | Mapping[str, Any],
    field_events: Iterable[object],
    *,
    collection_id: str = "field-evidence-001",
) -> FieldEvidenceCollection:
    normalized_dispatch = _normalize_dispatch(dispatch)
    if not normalized_dispatch.verified:
        raise FieldEvidenceError("dispatch decision must be verified")
    events = tuple(field_events) or tuple()
    if not events:
        raise FieldEvidenceError("field events are required")
    return FieldEvidenceCollection(
        collection_id=collection_id,
        operation_id=normalized_dispatch.request.operation_id,
        dispatch_hash=normalized_dispatch.decision_hash,
        selected_participant_id=normalized_dispatch.selected_participant_id,
        field_events=events,
    )


def ingest_field_evidence_signal(signal: FieldEvidenceSignal | Mapping[str, Any]) -> FieldEvent:
    normalized = signal if isinstance(signal, FieldEvidenceSignal) else FieldEvidenceSignal.from_mapping(signal)
    return normalized.to_field_event()


def ingest_field_evidence_signals(
    dispatch: DispatchDecision | Mapping[str, Any],
    signals: Iterable[FieldEvidenceSignal | Mapping[str, Any]],
    *,
    ingestion_id: str = "field-evidence-ingestion-001",
    collection_id: str = "field-evidence-001",
) -> FieldEvidenceIngestionResult:
    normalized_dispatch = _normalize_dispatch(dispatch)
    if not normalized_dispatch.verified:
        raise FieldEvidenceError("dispatch decision must be verified")

    normalized_signals = tuple(
        signal if isinstance(signal, FieldEvidenceSignal) else FieldEvidenceSignal.from_mapping(signal)
        for signal in signals
    )
    if not normalized_signals:
        raise FieldEvidenceError("field evidence signals are required")

    source_ids = {signal.source_id for signal in normalized_signals}
    if len(source_ids) != 1:
        raise FieldEvidenceError("field evidence signals must come from one source")
    signal_ids = [signal.signal_id for signal in normalized_signals]
    if len(set(signal_ids)) != len(signal_ids):
        raise FieldEvidenceError("duplicate field evidence signal_id")

    expected_operation_id = normalized_dispatch.request.operation_id
    expected_participant_id = normalized_dispatch.selected_participant_id
    for signal in normalized_signals:
        if signal.operation_id != expected_operation_id:
            raise FieldEvidenceError("field evidence signal operation_id mismatch")
        if signal.participant_id != expected_participant_id:
            raise FieldEvidenceError("field evidence signal participant_id mismatch")

    ordered = tuple(
        sorted(
            normalized_signals,
            key=lambda signal: (
                signal.received_at,
                CANONICAL_FIELD_EVENT_TYPES.index(signal.event_type),
                signal.signal_id,
                signal.signal_hash,
            ),
        )
    )
    events = tuple(signal.to_field_event() for signal in ordered)
    collection = build_field_evidence_collection(
        normalized_dispatch,
        events,
        collection_id=collection_id,
    )
    proof = build_field_evidence_proof(collection)
    invariant_report = evaluate_field_evidence_invariants(collection, proof, normalized_dispatch)
    validate_field_evidence_invariants(invariant_report)
    return FieldEvidenceIngestionResult(
        ingestion_id=_require_text(ingestion_id, "ingestion_id"),
        source_id=ordered[0].source_id,
        signal_hashes=tuple(signal.signal_hash for signal in ordered),
        collection=collection,
        proof=proof,
        invariant_report=invariant_report,
    )


def build_field_evidence_proof(collection: FieldEvidenceCollection | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_collection(collection)
    proof = {
        "schema": "afritech.mobility.field_evidence_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "collection_hash": normalized.collection_hash,
        "collection_id": normalized.collection_id,
        "dispatch_hash": normalized.dispatch_hash,
        "field_events": [event.canonical_dict() for event in normalized.field_events],
        "operation_id": normalized.operation_id,
        "selected_participant_id": normalized.selected_participant_id,
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def _validate_sequence(collection: FieldEvidenceCollection) -> None:
    observed = tuple(event.event_type for event in collection.field_events)
    if observed != CANONICAL_FIELD_EVENT_TYPES:
        raise FieldEvidenceError("field event sequence mismatch")


def _validate_motion(collection: FieldEvidenceCollection) -> None:
    previous: FieldEvent | None = None
    for event in collection.field_events:
        if not (-90.0 <= event.location.lat <= 90.0):
            raise FieldEvidenceError("latitude out of bounds")
        if not (-180.0 <= event.location.lon <= 180.0):
            raise FieldEvidenceError("longitude out of bounds")
        if previous is not None:
            if event.timestamp < previous.timestamp:
                raise FieldEvidenceError("field events must be replay-stable")
            distance = _haversine_km(previous.location, event.location)
            delta = event.timestamp - previous.timestamp
            if distance > MAX_GPS_JUMP_KM and delta <= MAX_GPS_JUMP_SECONDS:
                raise FieldEvidenceError("unrealistic field movement detected")
        previous = event


def evaluate_field_evidence_invariants(
    collection: FieldEvidenceCollection | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> FieldEvidenceInvariantReport:
    normalized = _coerce_collection(collection)
    actual_proof = proof if proof is not None else build_field_evidence_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise FieldEvidenceError("proof must be a mapping")
    normalized_dispatch = _normalize_dispatch(dispatch)
    expected_participant_id = (
        normalized_dispatch.selected_participant_id if normalized_dispatch is not None else normalized.selected_participant_id
    )
    expected_operation_id = normalized_dispatch.request.operation_id if normalized_dispatch is not None else normalized.operation_id
    expected_dispatch_hash = normalized_dispatch.decision_hash if normalized_dispatch is not None else normalized.dispatch_hash

    round_tripped = FieldEvidenceCollection.from_mapping(normalized.canonical_dict())
    _validate_sequence(normalized)
    _validate_motion(normalized)

    checks = (
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-001",
            satisfied=normalized.collection_hash == normalized.canonical_dict()["collection_hash"] and actual_proof.get("proof_hash") is not None,
            details="field evidence remains hash-verifiable",
            evidence_hash=normalized.collection_hash,
        ),
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-002",
            satisfied=round_tripped.collection_hash == normalized.collection_hash and [event.event_id for event in round_tripped.field_events] == [event.event_id for event in normalized.field_events],
            details="field evidence ordering remains replay-stable",
            evidence_hash=normalized.collection_hash,
        ),
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-003",
            satisfied=all(event.operation_id == normalized.operation_id for event in normalized.field_events)
            and actual_proof.get("operation_id") == expected_operation_id
            and actual_proof.get("dispatch_hash") == expected_dispatch_hash,
            details="field evidence remains bound to the operation and dispatch",
            evidence_hash=normalized.collection_hash,
        ),
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-004",
            satisfied=all(-90.0 <= event.location.lat <= 90.0 and -180.0 <= event.location.lon <= 180.0 for event in normalized.field_events),
            details="field evidence location remains bounded",
            evidence_hash=normalized.collection_hash,
        ),
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-005",
            satisfied=all(event.verified for event in normalized.field_events) and normalized.verified,
            details="field evidence remains immutable and verified",
            evidence_hash=normalized.collection_hash,
        ),
        FieldEvidenceInvariantCheck(
            identifier="IA-FIELD-006",
            satisfied=(
                normalized.authority_boundary == AUTHORITY_BOUNDARY
                and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY
                and actual_proof.get("selected_participant_id") == expected_participant_id
            ),
            details="field evidence remains input only",
            evidence_hash=normalized.collection_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "collection_hash": normalized.collection_hash,
            "proof_schema": "afritech.mobility.field_evidence_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return FieldEvidenceInvariantReport(
        collection_hash=normalized.collection_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_field_evidence_invariants(report: FieldEvidenceInvariantReport) -> bool:
    if not isinstance(report, FieldEvidenceInvariantReport):
        raise FieldEvidenceError("report must be a FieldEvidenceInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise FieldEvidenceError("field evidence invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise FieldEvidenceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise FieldEvidenceError(f"{check.identifier} failed: {check.details}")
    return True


def validate_field_evidence(
    collection: FieldEvidenceCollection | Mapping[str, Any],
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> bool:
    normalized_dispatch = _normalize_dispatch(dispatch)
    if isinstance(collection, Mapping):
        payload = dict(collection)
        if "collection_hash" not in payload:
            raise FieldEvidenceError("collection_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            record_payload.pop("proof_hash", None)
            normalized = FieldEvidenceCollection.from_mapping(record_payload)
            if payload.get("collection_hash") != normalized.collection_hash:
                raise FieldEvidenceError("collection_hash mismatch")
            if normalized_dispatch is not None:
                if payload.get("selected_participant_id") != normalized_dispatch.selected_participant_id:
                    raise FieldEvidenceError("selected_participant_id mismatch")
                if payload.get("operation_id") != normalized_dispatch.request.operation_id:
                    raise FieldEvidenceError("operation_id mismatch")
                if payload.get("dispatch_hash") != normalized_dispatch.decision_hash:
                    raise FieldEvidenceError("dispatch_hash mismatch")
            proof_payload = build_field_evidence_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise FieldEvidenceError("proof_hash mismatch")
        else:
            normalized = FieldEvidenceCollection.from_mapping(payload)
            if payload.get("collection_hash") != normalized.collection_hash:
                raise FieldEvidenceError("collection_hash mismatch")
            if normalized_dispatch is not None:
                if payload.get("selected_participant_id") != normalized_dispatch.selected_participant_id:
                    raise FieldEvidenceError("selected_participant_id mismatch")
                if payload.get("operation_id") != normalized_dispatch.request.operation_id:
                    raise FieldEvidenceError("operation_id mismatch")
                if payload.get("dispatch_hash") != normalized_dispatch.decision_hash:
                    raise FieldEvidenceError("dispatch_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_field_evidence_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise FieldEvidenceError("proof_hash mismatch")
    else:
        normalized = _coerce_collection(collection)

    proof = build_field_evidence_proof(normalized)
    report = evaluate_field_evidence_invariants(normalized, proof, normalized_dispatch)
    validate_field_evidence_invariants(report)
    return True


def validate_field_evidence_ingestion(result: FieldEvidenceIngestionResult | Mapping[str, Any]) -> bool:
    if isinstance(result, FieldEvidenceIngestionResult):
        normalized = result
    elif isinstance(result, Mapping):
        if result.get("schema") != FIELD_EVIDENCE_INGESTION_SCHEMA:
            raise FieldEvidenceError("field evidence ingestion schema mismatch")
        if result.get("authority_boundary") != INGESTION_AUTHORITY_BOUNDARY:
            raise FieldEvidenceError("field evidence ingestion authority boundary mismatch")
        collection = FieldEvidenceCollection.from_mapping(result.get("collection", {}))
        proof = result.get("proof")
        if not isinstance(proof, Mapping):
            raise FieldEvidenceError("field evidence ingestion proof must be a mapping")
        report_payload = result.get("invariant_report")
        if not isinstance(report_payload, Mapping):
            raise FieldEvidenceError("field evidence ingestion invariant report must be a mapping")
        checks = tuple(
            FieldEvidenceInvariantCheck(
                identifier=str(check["identifier"]),
                satisfied=bool(check["satisfied"]),
                details=str(check["details"]),
                evidence_hash=str(check["evidence_hash"]),
            )
            for check in report_payload.get("checks", ())
            if isinstance(check, Mapping)
        )
        invariant_report = FieldEvidenceInvariantReport(
            collection_hash=str(report_payload.get("collection_hash")),
            proof_hash=str(report_payload.get("proof_hash")),
            check_hash=str(report_payload.get("check_hash")),
            checks=checks,
            authority_boundary=str(report_payload.get("authority_boundary")),
        )
        normalized = FieldEvidenceIngestionResult(
            ingestion_id=str(result.get("ingestion_id")),
            source_id=str(result.get("source_id")),
            signal_hashes=tuple(str(value) for value in result.get("signal_hashes", ())),
            collection=collection,
            proof=proof,
            invariant_report=invariant_report,
            authority_boundary=str(result.get("authority_boundary")),
        )
        if result.get("ingestion_hash") != normalized.ingestion_hash:
            raise FieldEvidenceError("field evidence ingestion_hash mismatch")
    else:
        raise FieldEvidenceError("result must be a FieldEvidenceIngestionResult or mapping")

    if not normalized.verified:
        raise FieldEvidenceError("field evidence ingestion result is not verified")
    embedded_signal_hashes = tuple(
        str(dict(event.payload).get("signal_hash"))
        for event in normalized.collection.field_events
    )
    if embedded_signal_hashes != normalized.signal_hashes:
        raise FieldEvidenceError("field evidence signal hashes do not match event payloads")
    validate_field_evidence(normalized.collection)
    validate_field_evidence_invariants(normalized.invariant_report)
    return True


def export_field_evidence(
    output_dir: str | Path,
    collection: FieldEvidenceCollection | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_collection(collection)
    proof = build_field_evidence_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "field_evidence.json"
    proof_path = target / "field_evidence_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_field_evidence_invariant_report(
    output_dir: str | Path,
    collection: FieldEvidenceCollection | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_collection(collection)
    proof = build_field_evidence_proof(normalized)
    report = evaluate_field_evidence_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "field_evidence_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def export_field_evidence_ingestion(
    output_dir: str | Path,
    result: FieldEvidenceIngestionResult,
) -> dict[str, Path]:
    validate_field_evidence_ingestion(result)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    ingestion_path = target / "field_evidence_ingestion.json"
    collection_path = target / "field_evidence.json"
    proof_path = target / "field_evidence_proof.json"
    report_path = target / "field_evidence_invariant_report.json"
    ingestion_path.write_text(json.dumps(result.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    collection_path.write_text(json.dumps(result.collection.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(dict(result.proof), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(result.invariant_report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {
        "ingestion": ingestion_path,
        "json": collection_path,
        "proof": proof_path,
        "report": report_path,
    }


__all__ = [
    "AUTHORITY_BOUNDARY",
    "CANONICAL_FIELD_EVENT_TYPES",
    "FIELD_EVIDENCE_INGESTION_SCHEMA",
    "FIELD_EVIDENCE_SIGNAL_SCHEMA",
    "FieldEvidenceCollection",
    "FieldEvidenceError",
    "FieldEvidenceIngestionResult",
    "FieldEvidenceInvariantCheck",
    "FieldEvidenceInvariantReport",
    "FieldEvidenceSignal",
    "FieldEvidenceValidationReport",
    "FieldEvent",
    "INGESTION_AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "MAX_GPS_JUMP_KM",
    "MAX_GPS_JUMP_SECONDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_field_evidence_collection",
    "build_field_evidence_proof",
    "evaluate_field_evidence_invariants",
    "export_field_evidence",
    "export_field_evidence_ingestion",
    "export_field_evidence_invariant_report",
    "ingest_field_evidence_signal",
    "ingest_field_evidence_signals",
    "validate_field_evidence",
    "validate_field_evidence_ingestion",
    "validate_field_evidence_invariants",
]
