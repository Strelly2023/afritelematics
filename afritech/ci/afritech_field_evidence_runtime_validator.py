"""Validate ADR-0042 field evidence runtime ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.field_evidence import (
    CANONICAL_FIELD_EVENT_TYPES,
    FieldEvidenceError,
    ingest_field_evidence_signal,
    ingest_field_evidence_signals,
    validate_field_evidence_ingestion,
)
from afritech.mobility.trust_dispatch import (
    DispatchCandidate,
    DispatchRequest,
    run_trust_aware_dispatch,
)


class AfriTechFieldEvidenceRuntimeValidationError(RuntimeError):
    """Raised when ADR-0042 runtime ingestion is invalid."""


@dataclass(frozen=True)
class AfriTechFieldEvidenceRuntimeReport:
    event_count: int
    signal_count: int
    collection_hash: str
    proof_hash: str
    ingestion_hash: str
    authority_boundary: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_boundary": self.authority_boundary,
            "collection_hash": self.collection_hash,
            "event_count": self.event_count,
            "ingestion_hash": self.ingestion_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.field_evidence_runtime_report.v1",
            "signal_count": self.signal_count,
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _hash(self.canonical_dict())


def validate() -> AfriTechFieldEvidenceRuntimeReport:
    dispatch = _dispatch()
    signals = _field_signals(dispatch)

    first_event = ingest_field_evidence_signal(signals[0])
    if first_event.event_type != "GPS":
        raise AfriTechFieldEvidenceRuntimeValidationError(
            "first field signal did not produce GPS field event"
        )
    if dict(first_event.payload).get("source_id") != "pilot-phone-001":
        raise AfriTechFieldEvidenceRuntimeValidationError(
            "first field signal source binding missing"
        )

    result = ingest_field_evidence_signals(
        dispatch,
        reversed(signals),
        ingestion_id="adr-0042-runtime-validation",
        collection_id="adr-0042-field-evidence-runtime",
    )
    if not validate_field_evidence_ingestion(result):
        raise AfriTechFieldEvidenceRuntimeValidationError(
            "field evidence ingestion did not validate"
        )
    if tuple(event.event_type for event in result.collection.field_events) != CANONICAL_FIELD_EVENT_TYPES:
        raise AfriTechFieldEvidenceRuntimeValidationError(
            "field evidence runtime event sequence mismatch"
        )
    _assert_authority_injection_rejected(dispatch, signals)
    _assert_dispatch_override_rejected(dispatch, signals)

    report = AfriTechFieldEvidenceRuntimeReport(
        event_count=len(result.collection.field_events),
        signal_count=len(result.signal_hashes),
        collection_hash=result.collection.collection_hash,
        proof_hash=str(result.proof["proof_hash"]),
        ingestion_hash=result.ingestion_hash,
        authority_boundary=result.authority_boundary,
        verified=result.verified,
    )
    if not report.verified:
        raise AfriTechFieldEvidenceRuntimeValidationError(
            "field evidence runtime report failed"
        )
    return report


def _dispatch():
    request = DispatchRequest.from_mapping(
        {
            "operation_id": "op-adr-0042-runtime",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_100},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": "driver-adr-0042-runtime",
            "display_name": "ADR-0042 Runtime Driver",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 95.0,
            "evidence_links": ["adr-0042-runtime-driver"],
            "metadata": {},
        }
    )
    candidate = DispatchCandidate.from_mapping(
        {
            "participant": participant.canonical_dict(),
            "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "availability": True,
            "reliability_score": 95.0,
            "anomaly_rate": 0.0,
            "supported_operations": ["ride"],
            "capacity": 1,
            "metadata": {},
        }
    )
    return run_trust_aware_dispatch(request, (candidate,))


def _field_signals(dispatch) -> tuple[dict[str, Any], ...]:
    participant_id = dispatch.selected_participant_id
    operation_id = dispatch.request.operation_id
    base = (
        ("GPS", 1_700_000_000, {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000}, {"speed": 0}),
        ("DRIVER_ACCEPT", 1_700_000_010, {"lat": -37.8137, "lon": 144.9632, "timestamp": 1_700_000_010}, {"accepted": True}),
        ("ARRIVAL", 1_700_000_120, {"lat": -37.8138, "lon": 144.9633, "timestamp": 1_700_000_120}, {"arrived": True}),
        ("PICKUP", 1_700_000_180, {"lat": -37.8139, "lon": 144.9634, "timestamp": 1_700_000_180}, {"passenger_onboard": True}),
        ("DROPOFF", 1_700_000_900, {"lat": -37.8140, "lon": 144.9635, "timestamp": 1_700_000_900}, {"passenger_offboard": True}),
        ("CUSTOMER_CONFIRM", 1_700_000_930, {"lat": -37.8141, "lon": 144.9636, "timestamp": 1_700_000_930}, {"confirmed": True}),
        ("PAYMENT_CONFIRM", 1_700_000_960, {"lat": -37.8142, "lon": 144.9637, "timestamp": 1_700_000_960}, {"paid": True}),
    )
    return tuple(
        {
            "signal_id": f"{operation_id}-{event_type.lower()}",
            "source_id": "pilot-phone-001",
            "source_adapter_version": "adr-0042-mobile-v1",
            "operation_id": operation_id,
            "participant_id": participant_id,
            "event_type": event_type,
            "observed_at": timestamp - 1,
            "received_at": timestamp,
            "location": location,
            "payload": payload,
        }
        for event_type, timestamp, location, payload in base
    )


def _assert_authority_injection_rejected(dispatch, signals: tuple[dict[str, Any], ...]) -> None:
    tampered = [dict(signal) for signal in signals]
    tampered[0] = {**tampered[0], "payload": {**dict(tampered[0]["payload"]), "replay_hash": "0" * 64}}
    try:
        ingest_field_evidence_signals(dispatch, tampered)
    except FieldEvidenceError:
        return
    raise AfriTechFieldEvidenceRuntimeValidationError(
        "field evidence runtime admitted replay authority injection"
    )


def _assert_dispatch_override_rejected(dispatch, signals: tuple[dict[str, Any], ...]) -> None:
    tampered = [dict(signal) for signal in signals]
    tampered[0]["participant_id"] = "driver-not-selected"
    try:
        ingest_field_evidence_signals(dispatch, tampered)
    except FieldEvidenceError:
        return
    raise AfriTechFieldEvidenceRuntimeValidationError(
        "field evidence runtime admitted dispatch override"
    )


def _hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except AfriTechFieldEvidenceRuntimeValidationError as exc:
        print(f"AfriTech field evidence runtime validation FAILED: {exc}")
        return 1

    print(
        "AfriTech field evidence runtime validation PASSED: "
        f"signals={report.signal_count} "
        f"events={report.event_count} "
        f"collection_hash={report.collection_hash} "
        f"proof_hash={report.proof_hash} "
        f"ingestion_hash={report.ingestion_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
