from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from ecosystems.afriride.geo.types import GeoPoint

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.trust_dispatch import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    DispatchCandidate,
    DispatchCandidateError,
    DispatchDecisionError,
    DispatchRequest,
    DispatchRequestError,
    build_dispatch_decision_proof,
    export_dispatch_decision_proof,
    run_trust_aware_dispatch,
    validate_dispatch_decision,
)
from afritech.mobility.trust_dispatch_invariants import (
    DispatchInvariantError,
    evaluate_dispatch_invariants,
    validate_dispatch_invariants,
)


def _request() -> DispatchRequest:
    return DispatchRequest.from_mapping(
        {
            "operation_id": "dispatch-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.6733, "lon": 144.8433, "timestamp": 1_700_000_900},
            "constraints": {"required_roles": ["driver"], "minimum_capacity": 1},
            "timestamp": 1_700_000_000,
        }
    )


def _candidate(
    participant_id: str,
    trust_score: float,
    reliability_score: float,
    anomaly_rate: float,
    lat: float,
    lon: float,
    supported_operations: tuple[str, ...] = ("ride",),
) -> DispatchCandidate:
    return DispatchCandidate.from_mapping(
        {
            "participant": {
                "participant_id": participant_id,
                "display_name": participant_id,
                "roles": ["driver"],
                "verification_status": "verified",
                "trust_score": trust_score,
                "evidence_links": [f"ev-{participant_id}"],
                "metadata": {},
            },
            "location": {"lat": lat, "lon": lon, "timestamp": 1_700_000_000},
            "availability": True,
            "reliability_score": reliability_score,
            "anomaly_rate": anomaly_rate,
            "supported_operations": list(supported_operations),
            "capacity": 1,
            "metadata": {},
        }
    )


def test_dispatch_happy_path():
    request = _request()
    candidates = (
        _candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),
        _candidate("driver-b", 95, 96, 2, -37.7000, 144.9000),
    )

    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.selected_participant_id == "driver-a"
    assert decision.canonical_dict()["schema"] == SCHEMA


def test_dispatch_invalid_input():
    with pytest.raises(DispatchRequestError):
        DispatchRequest.from_mapping({"operation_type": "ride"})

    with pytest.raises(DispatchCandidateError):
        DispatchCandidate.from_mapping({"participant": None})


def test_dispatch_determinism():
    request = _request()
    candidates = (_candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),)

    a = run_trust_aware_dispatch(request, candidates)
    b = run_trust_aware_dispatch(request, candidates)

    assert a.canonical_dict() == b.canonical_dict()
    assert a.decision_hash == b.decision_hash


def test_dispatch_replay_stability():
    request = _request()
    candidates = (_candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),)

    decision = run_trust_aware_dispatch(request, candidates)
    replay = run_trust_aware_dispatch(request, candidates)

    assert decision.decision_hash == replay.decision_hash
    assert decision.canonical_dict() == replay.canonical_dict()


def test_dispatch_serialization():
    request = _request()
    candidates = (_candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),)

    decision = run_trust_aware_dispatch(request, candidates)
    decoded = json.loads(json.dumps(decision.canonical_dict(), sort_keys=True))

    assert decoded["selected_participant_id"] == "driver-a"
    assert decoded["decision_hash"] == decision.decision_hash


def test_high_trust_selected_over_lower():
    request = _request()
    candidates = (
        _candidate("driver-low", 60, 95, 2, -37.8136, 144.9631),
        _candidate("driver-high", 95, 95, 2, -37.8136, 144.9631),
    )

    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.selected_participant_id == "driver-high"


def test_equal_conditions_deterministic_order():
    request = _request()
    candidates = (
        _candidate("driver-a", 90, 90, 5, -37.8136, 144.9631),
        _candidate("driver-b", 90, 90, 5, -37.8136, 144.9631),
    )

    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.ranked_candidates[0].participant_id == "driver-a"


def test_anomaly_penalty_applied():
    request = _request()
    candidates = (
        _candidate("driver-clean", 90, 90, 1, -37.8136, 144.9631),
        _candidate("driver-noisy", 90, 90, 40, -37.8136, 144.9631),
    )

    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.selected_participant_id == "driver-clean"


def test_dispatch_authority_boundary():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)

    assert decision.authority_boundary == AUTHORITY_BOUNDARY
    assert decision.canonical_dict()["authority_boundary"] == AUTHORITY_BOUNDARY


def test_dispatch_no_external_mutation():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)
    tampered = deepcopy(decision.canonical_dict())
    tampered["selected_participant_id"] = "driver-b"

    assert tampered != decision.canonical_dict()


def test_dispatch_invariant_compliance():
    request = _request()
    candidates = (
        _candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),
        _candidate("driver-b", 95, 96, 2, -37.7000, 144.9000),
    )
    decision = run_trust_aware_dispatch(request, candidates)
    report = evaluate_dispatch_invariants(request, candidates, decision)

    assert report.verified is True
    assert validate_dispatch_invariants(report) is True


def test_missing_candidate_detection():
    request = _request()
    full_candidates = (
        _candidate("driver-a", 99, 98, 1, -37.8136, 144.9631),
        _candidate("driver-b", 95, 96, 2, -37.8136, 144.9631),
    )
    reduced_candidates = full_candidates[:1]

    with pytest.raises(DispatchDecisionError):
        validate_dispatch_decision(request, reduced_candidates, run_trust_aware_dispatch(request, full_candidates))


def test_tampered_evidence_fails():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)
    tampered = deepcopy(decision.canonical_dict())
    tampered["evidence"]["selected_id"] = "driver-b"

    with pytest.raises(DispatchDecisionError):
        validate_dispatch_decision(request, candidates, tampered)


def test_score_manipulation_detected():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)
    tampered = deepcopy(decision.canonical_dict())
    tampered["ranked_candidates"][0]["score"] = 0.0

    with pytest.raises(DispatchDecisionError):
        validate_dispatch_decision(request, candidates, tampered)


def test_dispatch_proof_artifact_roundtrip(tmp_path):
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)

    proof = build_dispatch_decision_proof(decision)
    exported = export_dispatch_decision_proof(decision, tmp_path)

    assert proof["verified"] is True
    assert proof["schema"] == "afritech.mobility.dispatch_decision_proof.v1"
    assert exported["json"].exists()


def test_dispatch_validator_rejects_bad_request():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)

    bad_request = deepcopy(request.canonical_dict())
    bad_request["operation_type"] = "invalid"

    with pytest.raises((DispatchRequestError, DispatchDecisionError)):
        validate_dispatch_decision(bad_request, candidates, decision)


def test_dispatch_invariant_validator_rejects_bad_report():
    request = _request()
    candidates = (_candidate("driver-a", 99, 99, 0, -37.8136, 144.9631),)
    decision = run_trust_aware_dispatch(request, candidates)
    report = evaluate_dispatch_invariants(request, candidates, decision)
    tampered = replace(report, checks=tuple())

    with pytest.raises(DispatchInvariantError):
        validate_dispatch_invariants(tampered)
