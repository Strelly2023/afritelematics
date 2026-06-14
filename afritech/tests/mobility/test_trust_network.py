from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch
from afritech.mobility.trust_network import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    TrustNetworkError,
    TrustProfile,
    TrustUpdateEvent,
    build_trust_profile,
    build_trust_profile_proof,
    export_trust_profile_proof,
    evaluate_trust_invariants,
    update_trust_profile,
    validate_trust_invariants,
    validate_trust_profile,
)


def _event(
    event_id: str,
    event_type: str,
    *,
    participant_id: str = "participant-001",
    source_operation_id: str = "operation-001",
    timestamp: int = 1_700_000_000,
    rating: float | None = None,
) -> TrustUpdateEvent:
    return TrustUpdateEvent.from_mapping(
        {
            "event_id": event_id,
            "participant_id": participant_id,
            "event_type": event_type,
            "source_operation_id": source_operation_id,
            "dispatch_hash": "a" * 64,
            "custody_hash": "b" * 64,
            "settlement_hash": "c" * 64,
            "evidence_link": f"evidence-{event_id}",
            "timestamp": timestamp,
            "rating": rating,
            "verified": True,
            "metadata": {},
        }
    )


def _history() -> tuple[TrustUpdateEvent, ...]:
    return (
        _event("event-001", "successful_delivery", rating=5.0),
        _event("event-002", "settlement_completed", timestamp=1_700_000_100, rating=4.5),
        _event("event-003", "dispute_resolved", timestamp=1_700_000_200, rating=3.5),
    )


def test_trust_profile_happy_path():
    profile = build_trust_profile("participant-001", _history())

    assert profile.participant_id == "participant-001"
    assert profile.canonical_dict()["schema"] == SCHEMA
    assert 0.0 <= profile.trust_score <= 100.0


def test_trust_invalid_input():
    with pytest.raises(TrustNetworkError):
        TrustUpdateEvent.from_mapping({"event_type": "successful_delivery"})

    with pytest.raises(TrustNetworkError):
        build_trust_profile("", _history())


def test_trust_determinism():
    a = build_trust_profile("participant-001", _history())
    b = build_trust_profile("participant-001", _history())

    assert a.canonical_dict() == b.canonical_dict()
    assert a.profile_hash == b.profile_hash


def test_trust_replay_produces_same_score():
    profile = build_trust_profile("participant-001", _history())
    replay = build_trust_profile("participant-001", profile.event_history)

    assert profile.trust_score == replay.trust_score
    assert profile.profile_hash == replay.profile_hash


def test_event_order_affects_score():
    profile = build_trust_profile("participant-001", _history())
    reordered = build_trust_profile("participant-001", tuple(reversed(_history())))

    assert profile.trust_score != reordered.trust_score or profile.profile_hash != reordered.profile_hash


def test_trust_tampering_detected():
    profile = build_trust_profile("participant-001", _history())
    tampered = deepcopy(profile.canonical_dict())
    tampered["event_history"][0]["event_type"] = "delay_reported"

    with pytest.raises(TrustNetworkError):
        validate_trust_profile(tampered)


def test_invalid_event_rejected():
    with pytest.raises(TrustNetworkError):
        TrustUpdateEvent.from_mapping(
            {
                "event_id": "event-bad",
                "participant_id": "participant-001",
                "event_type": "invalid_event",
                "source_operation_id": "operation-001",
                "dispatch_hash": "a" * 64,
                "custody_hash": "b" * 64,
                "settlement_hash": "c" * 64,
                "evidence_link": "evidence-bad",
                "timestamp": 1_700_000_000,
                "verified": True,
            }
        )


def test_trust_not_authority():
    profile = build_trust_profile("participant-001", _history())

    assert profile.authority_boundary == AUTHORITY_BOUNDARY
    assert profile.canonical_dict()["identity_is_reference_only"] is True
    assert profile.canonical_dict()["identity_is_truth_authority"] is False
    assert profile.canonical_dict()["identity_overrides_proof"] is False
    assert profile.canonical_dict()["identity_overrides_replay"] is False
    assert profile.canonical_dict()["identity_overrides_payment"] is False
    assert profile.canonical_dict()["identity_overrides_runtime_admissibility"] is False


def test_trust_bounds_enforced():
    many_events = tuple(
        _event(
            f"event-{index:03d}",
            "successful_delivery" if index % 2 == 0 else "settlement_completed",
            timestamp=1_700_000_000 + index * 10,
            rating=5.0,
        )
        for index in range(40)
    )
    profile = build_trust_profile("participant-001", many_events)

    assert 0.0 <= profile.trust_score <= 100.0


def test_trust_serialization_roundtrip():
    profile = build_trust_profile("participant-001", _history())
    decoded = json.loads(json.dumps(profile.canonical_dict(), sort_keys=True))

    assert decoded["profile_hash"] == profile.profile_hash
    assert decoded["trust_score"] == round(profile.trust_score, 6)


def test_trust_invariant_compliance():
    profile = build_trust_profile("participant-001", _history())
    report = evaluate_trust_invariants(profile)

    assert report.verified is True
    assert validate_trust_invariants(report) is True


def test_trust_profile_proof_artifact_roundtrip(tmp_path):
    profile = build_trust_profile("participant-001", _history())
    proof = build_trust_profile_proof(profile)
    exported = export_trust_profile_proof(profile, tmp_path)

    assert proof["verified"] is True
    assert proof["schema"] == "afritech.mobility.trust_profile_proof.v1"
    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_trust_update_changes_profile():
    profile = build_trust_profile("participant-001", _history())
    updated = update_trust_profile(profile, _event("event-004", "successful_pickup", timestamp=1_700_000_300))

    assert updated.total_operations == profile.total_operations + 1
    assert updated.trust_score != profile.trust_score


def test_trust_profile_feeds_dispatch():
    profile = build_trust_profile("participant-001", _history())
    participant = profile.to_mobility_participant(
        display_name="Participant One",
        roles=("driver",),
        verification_status="verified",
    )

    assert isinstance(participant, MobilityParticipant)
    assert participant.trust_score == profile.trust_score

    request = DispatchRequest.from_mapping(
        {
            "operation_id": "dispatch-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_500},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
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

    decision = run_trust_aware_dispatch(request, (candidate,))

    assert decision.selected_participant_id == participant.participant_id


def test_missing_evidence_fails_visible():
    with pytest.raises(TrustNetworkError):
        TrustUpdateEvent.from_mapping(
            {
                "event_id": "event-bad",
                "participant_id": "participant-001",
                "event_type": "successful_delivery",
                "source_operation_id": "operation-001",
                "dispatch_hash": "a" * 63,
                "custody_hash": "b" * 64,
                "settlement_hash": "c" * 64,
                "evidence_link": "evidence-bad",
                "timestamp": 1_700_000_000,
                "verified": True,
            }
        )


def test_trust_evidence_links_are_stable():
    profile = build_trust_profile("participant-001", _history())

    assert profile.evidence_links == tuple(sorted(profile.evidence_links))
    assert len(profile.evidence_links) == len(set(profile.evidence_links))
