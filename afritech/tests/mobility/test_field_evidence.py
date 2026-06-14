from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.field_evidence import (
    CANONICAL_FIELD_EVENT_TYPES,
    FieldEvidenceCollection,
    FieldEvidenceError,
    FieldEvidenceSignal,
    FieldEvent,
    build_field_evidence_collection,
    build_field_evidence_proof,
    evaluate_field_evidence_invariants,
    export_field_evidence,
    export_field_evidence_ingestion,
    export_field_evidence_invariant_report,
    ingest_field_evidence_signal,
    ingest_field_evidence_signals,
    validate_field_evidence,
    validate_field_evidence_ingestion,
    validate_field_evidence_invariants,
)
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch
from afritech.identity.mobility_participant import MobilityParticipant


def _dispatch():
    request = DispatchRequest.from_mapping(
        {
            "operation_id": "op-field-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_100},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": "driver-field-001",
            "display_name": "Field Driver",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 95.0,
            "evidence_links": ["driver-field-ev"],
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


def _field_events():
    dispatch = _dispatch()
    participant_id = dispatch.selected_participant_id
    operation_id = dispatch.request.operation_id
    base = [
        ("GPS", 1_700_000_000, {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000}, {"speed": 0}),
        ("DRIVER_ACCEPT", 1_700_000_010, {"lat": -37.8137, "lon": 144.9632, "timestamp": 1_700_000_010}, {"accepted": True}),
        ("ARRIVAL", 1_700_000_120, {"lat": -37.8138, "lon": 144.9633, "timestamp": 1_700_000_120}, {"arrived": True}),
        ("PICKUP", 1_700_000_180, {"lat": -37.8139, "lon": 144.9634, "timestamp": 1_700_000_180}, {"passenger_onboard": True}),
        ("DROPOFF", 1_700_000_900, {"lat": -37.8140, "lon": 144.9635, "timestamp": 1_700_000_900}, {"passenger_offboard": True}),
        ("CUSTOMER_CONFIRM", 1_700_000_930, {"lat": -37.8141, "lon": 144.9636, "timestamp": 1_700_000_930}, {"confirmed": True}),
        ("PAYMENT_CONFIRM", 1_700_000_960, {"lat": -37.8142, "lon": 144.9637, "timestamp": 1_700_000_960}, {"paid": True}),
    ]
    return [
        FieldEvent.from_mapping(
            {
                "event_id": f"{operation_id}-{event_type.lower()}",
                "operation_id": operation_id,
                "participant_id": participant_id,
                "event_type": event_type,
                "timestamp": timestamp,
                "location": location,
                "payload": payload,
            }
        )
        for event_type, timestamp, location, payload in base
    ]


def _field_signals():
    events = _field_events()
    return [
        {
            "signal_id": event.event_id,
            "source_id": "pilot-phone-001",
            "source_adapter_version": "adr-0042-mobile-v1",
            "operation_id": event.operation_id,
            "participant_id": event.participant_id,
            "event_type": event.event_type,
            "observed_at": event.timestamp - 1,
            "received_at": event.timestamp,
            "location": {
                "lat": event.location.lat,
                "lon": event.location.lon,
                "timestamp": event.timestamp - 1,
            },
            "payload": dict(event.payload),
        }
        for event in events
    ]


def _collection():
    dispatch = _dispatch()
    return build_field_evidence_collection(dispatch, _field_events())


def test_field_evidence_happy_path():
    collection = _collection()

    assert collection.collection_hash
    assert collection.field_events[0].event_type == "GPS"


def test_first_real_world_signal_becomes_field_event_without_authority():
    signal = FieldEvidenceSignal.from_mapping(_field_signals()[0])
    event = ingest_field_evidence_signal(signal)

    assert signal.signal_hash
    assert event.event_type == "GPS"
    assert event.authority_boundary == "field_evidence_reference_only"
    assert dict(event.payload)["signal_hash"] == signal.signal_hash
    assert dict(event.payload)["source_id"] == "pilot-phone-001"


def test_ingest_field_evidence_signals_builds_collection_proof_and_report():
    result = ingest_field_evidence_signals(_dispatch(), reversed(_field_signals()))
    data = result.canonical_dict()

    assert result.verified is True
    assert data["schema"] == "afritech.mobility.field_evidence_ingestion.v1"
    assert data["authority_boundary"] == "field_evidence_ingestion_read_only"
    assert data["collection_hash"] == result.collection.collection_hash
    assert data["proof_hash"] == result.proof["proof_hash"]
    assert validate_field_evidence_ingestion(result) is True
    assert [event.event_type for event in result.collection.field_events] == list(CANONICAL_FIELD_EVENT_TYPES)


def test_field_evidence_ingestion_round_trip_mapping_validates():
    result = ingest_field_evidence_signals(_dispatch(), _field_signals())

    assert validate_field_evidence_ingestion(result.canonical_dict()) is True


def test_field_evidence_ingestion_rejects_authority_injection():
    signals = _field_signals()
    signals[0]["payload"]["replay_hash"] = "0" * 64

    with pytest.raises(FieldEvidenceError):
        ingest_field_evidence_signals(_dispatch(), signals)


def test_field_evidence_ingestion_rejects_dispatch_override():
    signals = _field_signals()
    signals[0]["participant_id"] = "driver-not-selected"

    with pytest.raises(FieldEvidenceError):
        ingest_field_evidence_signals(_dispatch(), signals)


def test_export_field_evidence_ingestion(tmp_path):
    result = ingest_field_evidence_signals(_dispatch(), _field_signals())
    exported = export_field_evidence_ingestion(tmp_path, result)

    assert exported["ingestion"].exists()
    assert exported["json"].exists()
    assert exported["proof"].exists()
    assert exported["report"].exists()


def test_invalid_input_rejected():
    with pytest.raises(FieldEvidenceError):
        build_field_evidence_collection({}, [])  # type: ignore[arg-type]


def test_event_hash_stable():
    event = _field_events()[0]
    rebuilt = FieldEvent.from_mapping(event.canonical_dict())

    assert event.evidence_hash == rebuilt.evidence_hash


def test_event_order_replay():
    dispatch = _dispatch()
    events = list(reversed(_field_events()))
    collection = build_field_evidence_collection(dispatch, events)

    assert [event.event_id for event in collection.field_events] == [event.event_id for event in _field_events()]


def test_tampered_event_rejected():
    collection = _collection().canonical_dict()
    collection["field_events"][0]["payload"]["speed"] = 999  # type: ignore[index]

    with pytest.raises(FieldEvidenceError):
        validate_field_evidence(collection, dispatch=_dispatch())


def test_proof_tampering_rejected():
    collection = _collection()
    proof = build_field_evidence_proof(collection)
    proof["collection_hash"] = "f" * 64

    with pytest.raises(FieldEvidenceError):
        validate_field_evidence(proof, dispatch=_dispatch())


def test_field_event_must_match_dispatch_participant():
    collection = _collection().canonical_dict()
    dispatch = _dispatch().canonical_dict()
    dispatch["selected_participant_id"] = "driver-bad"

    with pytest.raises(FieldEvidenceError):
        validate_field_evidence(collection, dispatch=dispatch)


def test_unrealistic_jump_detected():
    collection = _collection().canonical_dict()
    collection["field_events"][4]["location"] = {"lat": -33.8688, "lon": 151.2093, "timestamp": 1_700_000_900}  # type: ignore[index]

    with pytest.raises(FieldEvidenceError):
        validate_field_evidence(collection, dispatch=_dispatch())


def test_missing_event_sequence_detected():
    dispatch = _dispatch()
    events = _field_events()[:-1]

    with pytest.raises(FieldEvidenceError):
        build_field_evidence_collection(dispatch, events)


def test_proof_integrity_round_trip():
    collection = _collection()
    proof = build_field_evidence_proof(collection)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["collection_hash"] == collection.collection_hash
    assert decoded["authority_boundary"] == "field_evidence_proof_read_only"


def test_export_field_evidence(tmp_path):
    collection = _collection()
    exported = export_field_evidence(tmp_path, collection)

    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_invariant_report():
    collection = _collection()
    proof = build_field_evidence_proof(collection)
    report = evaluate_field_evidence_invariants(collection, proof, _dispatch())

    assert report.verified is True
    assert validate_field_evidence_invariants(report) is True


def test_export_invariant_report(tmp_path):
    collection = _collection()
    exported = export_field_evidence_invariant_report(tmp_path, collection)

    assert exported["report"].exists()


def test_field_evidence_does_not_mutate_dispatch():
    dispatch = _dispatch()
    before = deepcopy(dispatch.canonical_dict())

    build_field_evidence_collection(dispatch, _field_events())

    assert dispatch.canonical_dict() == before


def test_canonical_event_types():
    assert CANONICAL_FIELD_EVENT_TYPES == (
        "GPS",
        "DRIVER_ACCEPT",
        "ARRIVAL",
        "PICKUP",
        "DROPOFF",
        "CUSTOMER_CONFIRM",
        "PAYMENT_CONFIRM",
    )
