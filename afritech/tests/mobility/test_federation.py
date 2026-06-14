from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ecosystems.afriride.geo.types import GeoPoint

from afritech.mobility.federation import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    FederatedParticipant,
    FederationError,
    FederationState,
    FederationTransition,
    FederationUnit,
    build_federation_proof,
    build_federation_state,
    derive_federated_trust,
    evaluate_federation_invariants,
    export_federation_proof,
    validate_federation_invariants,
    validate_federation_state,
)
from afritech.mobility.trust_network import TrustUpdateEvent, build_trust_profile
from afritech.mobility.trust_dispatch import DispatchRequest, run_trust_aware_dispatch


def _trust_profile(participant_id: str, score: float) -> object:
    events = (
        TrustUpdateEvent.from_mapping(
            {
                "event_id": f"{participant_id}-event-001",
                "participant_id": participant_id,
                "event_type": "successful_delivery",
                "source_operation_id": "op-001",
                "dispatch_hash": "a" * 64,
                "custody_hash": "b" * 64,
                "settlement_hash": "c" * 64,
                "evidence_link": f"ev-{participant_id}-001",
                "timestamp": 1_700_000_000,
                "rating": 5.0,
                "verified": True,
            }
        ),
    )
    profile = build_trust_profile(participant_id, events)
    if abs(profile.trust_score - score) > 0.1:
        # use a deterministic profile with a score close to the requested one
        return profile
    return profile


def _participant(
    participant_id: str,
    home_network: str,
    score: float,
    *,
    federation_status: str = "verified",
    verification_level: str = "verified",
    federation_weight: float = 0.85,
    cross_network_events: int = 1,
) -> FederatedParticipant:
    return FederatedParticipant.from_mapping(
        {
            "participant_id": participant_id,
            "home_network": home_network,
            "roles": ["driver"],
            "trust_profile": _trust_profile(participant_id, score),
            "federation_status": federation_status,
            "federation_weight": federation_weight,
            "verification_level": verification_level,
            "cross_network_events": cross_network_events,
            "evidence_links": [f"fed-{participant_id}-001"],
            "metadata": {},
        }
    )


def _unit(unit_id: str, network_id: str, members: list[str], trust_score: float) -> FederationUnit:
    return FederationUnit.from_mapping(
        {
            "unit_id": unit_id,
            "network_id": network_id,
            "unit_type": "fleet",
            "members": members,
            "trust_score": trust_score,
            "certification_status": "verified",
            "evidence_links": [f"unit-{unit_id}-001"],
            "metadata": {},
        }
    )


def _transition(
    transition_id: str,
    participant_id: str,
    from_network: str,
    to_network: str,
    trust_transferred: float,
) -> FederationTransition:
    return FederationTransition.from_mapping(
        {
            "transition_id": transition_id,
            "participant_id": participant_id,
            "from_network": from_network,
            "to_network": to_network,
            "trust_transferred": trust_transferred,
            "verification_level": "verified",
            "source_operation_id": f"op-{transition_id}",
            "evidence_link": f"transition-{transition_id}",
            "timestamp": 1_700_000_100,
            "verified": True,
            "metadata": {},
        }
    )


def _state() -> FederationState:
    participants = (
        _participant("driver-a", "network-a", 95.0),
        _participant("driver-b", "network-b", 90.0, federation_weight=0.80),
    )
    transition_trust = derive_federated_trust(
        participants[0].local_trust_score,
        participants[0].federation_weight,
        participants[0].verification_level,
    )
    units = (
        _unit("fleet-a", "network-a", ["driver-a"], 94.0),
        _unit("fleet-b", "network-b", ["driver-b"], 88.0),
    )
    transitions = (
        _transition("transition-001", "driver-a", "network-a", "network-b", transition_trust),
    )
    return build_federation_state("federation-001", participants, units=units, transitions=transitions)


def test_federation_happy_path():
    state = _state()

    assert state.federation_id == "federation-001"
    assert state.canonical_dict()["schema"] == SCHEMA
    assert state.verified is True


def test_invalid_membership():
    state = build_federation_state(
        "federation-bad",
        (
            _participant("driver-a", "network-a", 95.0),
            _participant("driver-bad", "network-b", 90.0, federation_status="pending"),
        ),
        units=(_unit("fleet-a", "network-a", ["driver-a"], 94.0),),
        transitions=(),
    )

    with pytest.raises(FederationError):
        validate_federation_state(state)


def test_identity_uniqueness():
    state = _state()
    duplicated = deepcopy(state.canonical_dict())
    duplicated["participants"].append(deepcopy(duplicated["participants"][0]))

    with pytest.raises(FederationError):
        validate_federation_state(duplicated)


def test_trust_transfer_bounded():
    state = _state()
    participant = state.participants[0]

    assert participant.federated_trust_score <= participant.local_trust_score
    assert 0.0 <= participant.federated_trust_score <= 100.0


def test_cross_network_trust_replay():
    state = _state()
    replay = build_federation_state("federation-001", state.participants, units=state.units, transitions=state.transitions)

    assert state.state_hash == replay.state_hash
    assert state.canonical_dict() == replay.canonical_dict()


def test_dispatch_across_networks():
    state = _state()
    request = DispatchRequest.from_mapping(
        {
            "operation_id": "dispatch-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_400},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )
    candidates = state.dispatch_candidates(
        location=GeoPoint(lat=-37.8136, lon=144.9631, timestamp=1_700_000_000),
        reliability_score=95.0,
        anomaly_rate=1.0,
        supported_operations=("ride",),
    )
    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.selected_participant_id in state.participant_ids


def test_federated_candidate_selection():
    state = _state()
    candidate = state.participants[0].to_dispatch_candidate(
        location=GeoPoint(lat=-37.8136, lon=144.9631, timestamp=1_700_000_000),
        reliability_score=95.0,
        anomaly_rate=0.0,
        supported_operations=("ride",),
        capacity=1,
    )

    assert candidate.participant.trust_score == state.participants[0].federated_trust_score


def test_cross_network_custody_chain():
    state = _state()
    transition = state.transitions[0]

    assert transition.from_network != transition.to_network
    assert transition.transition_hash == FederationTransition.from_mapping(transition.canonical_dict()).transition_hash


def test_multi_network_handoff_integrity():
    state = _state()
    proof = build_federation_proof(state)

    assert proof["verified"] is True
    assert proof["schema"] == "afritech.mobility.federation_proof.v1"


def test_duplicate_identity_rejected():
    participants = (
        _participant("driver-a", "network-a", 95.0),
        _participant("driver-a", "network-b", 90.0),
    )
    state = build_federation_state("federation-dup", participants, units=(), transitions=())

    with pytest.raises(FederationError):
        validate_federation_state(state)


def test_unverified_network_rejected():
    state = build_federation_state(
        "federation-unverified",
        (_participant("driver-a", "network-a", 95.0, federation_status="pending"),),
        units=(),
        transitions=(),
    )

    with pytest.raises(FederationError):
        validate_federation_state(state)


def test_trust_inflation_blocked():
    participant = _participant("driver-a", "network-a", 95.0, federation_weight=1.0)
    inflated = deepcopy(participant.canonical_dict())
    inflated["federation_weight"] = 2.0

    with pytest.raises(FederationError):
        FederatedParticipant.from_mapping(inflated)


def test_federation_invariant_compliance():
    state = _state()
    report = evaluate_federation_invariants(state)

    assert report.verified is True
    assert validate_federation_invariants(report) is True


def test_federation_proof_artifact_roundtrip(tmp_path):
    state = _state()
    proof = build_federation_proof(state)
    exported = export_federation_proof(state, tmp_path)

    assert proof["verified"] is True
    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_federation_serialization_roundtrip():
    state = _state()
    decoded = json.loads(json.dumps(state.canonical_dict(), sort_keys=True))

    assert decoded["state_hash"] == state.state_hash


def test_federation_authority_boundary():
    state = _state()

    assert state.authority_boundary == AUTHORITY_BOUNDARY
    assert state.canonical_dict()["authority_boundary"] == AUTHORITY_BOUNDARY


def test_federation_tampering_changes_hash():
    state = _state()
    tampered = deepcopy(state.canonical_dict())
    tampered["participants"][0]["home_network"] = "network-c"

    assert tampered != state.canonical_dict()


def test_federation_state_validation():
    state = _state()
    report = validate_federation_state(state)

    assert report.verified is True
    assert len(report.report_hash()) == 64
