from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.real_time_execution_engine import (
    RealTimeExecutionError,
    RealTimeExecutionRecord,
    ExecutionEvent,
    build_real_time_execution,
    build_real_time_execution_proof,
    evaluate_real_time_execution_invariants,
    export_real_time_execution,
    export_real_time_execution_invariant_report,
    validate_real_time_execution,
    validate_real_time_execution_invariants,
)
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch


def _dispatch():
    request = DispatchRequest.from_mapping(
        {
            "operation_id": "op-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_100},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": "driver-001",
            "display_name": "Driver One",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 95.0,
            "evidence_links": ["driver-001-ev"],
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


def _execution():
    return build_real_time_execution(_dispatch())


def test_execution_happy_path():
    execution = _execution()

    assert execution.execution_status == "COMPLETED"


def test_invalid_input():
    with pytest.raises(RealTimeExecutionError):
        build_real_time_execution({}, live_mode=True)  # type: ignore[arg-type]


def test_determinism():
    a = _execution()
    b = _execution()

    assert a.execution_hash == b.execution_hash


def test_replay_stability():
    execution = _execution()
    rebuilt = RealTimeExecutionRecord.from_mapping(execution.canonical_dict())

    assert execution.canonical_dict() == rebuilt.canonical_dict()


def test_authority_boundary():
    execution = _execution().canonical_dict()
    execution["authority_boundary"] = "override"

    with pytest.raises(RealTimeExecutionError):
        validate_real_time_execution(execution, dispatch=_dispatch())


def test_dispatch_binding_required():
    execution = _execution().canonical_dict()
    execution["dispatch_hash"] = "f" * 64

    with pytest.raises(RealTimeExecutionError):
        validate_real_time_execution(execution, dispatch=_dispatch())


def test_hash_tampering_detected():
    execution = _execution().canonical_dict()
    execution["execution_hash"] = "f" * 64

    with pytest.raises(RealTimeExecutionError):
        validate_real_time_execution(execution, dispatch=_dispatch())


def test_event_order_stability():
    execution = _execution()
    reordered = deepcopy(execution.canonical_dict())
    reordered["execution_events"] = list(reversed(reordered["execution_events"]))

    rebuilt = RealTimeExecutionRecord.from_mapping(reordered)
    assert execution.execution_hash == rebuilt.execution_hash


def test_proof_integrity_round_trip():
    execution = _execution()
    proof = build_real_time_execution_proof(execution)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["execution_hash"] == execution.execution_hash
    assert decoded["authority_boundary"] == "real_time_execution_proof_read_only"


def test_proof_hash_tampering_rejected(tmp_path):
    execution = _execution()
    exported = export_real_time_execution(tmp_path, execution)
    proof = json.loads(exported["proof"].read_text())
    proof["execution_hash"] = "f" * 64

    with pytest.raises(RealTimeExecutionError):
        validate_real_time_execution(proof, dispatch=_dispatch())


def test_execution_does_not_modify_dispatch():
    execution = _execution()

    assert execution.dispatch_hash == _dispatch().decision_hash


def test_export_real_time_execution(tmp_path):
    execution = _execution()
    exported = export_real_time_execution(tmp_path, execution)

    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_invariant_report():
    execution = _execution()
    proof = build_real_time_execution_proof(execution)
    report = evaluate_real_time_execution_invariants(execution, proof, _dispatch())

    assert report.verified is True
    assert validate_real_time_execution_invariants(report) is True


def test_export_invariant_report(tmp_path):
    execution = _execution()
    exported = export_real_time_execution_invariant_report(tmp_path, execution)

    assert exported["report"].exists()


def test_execution_participant_must_match_dispatch():
    execution = _execution().canonical_dict()
    dispatch = _dispatch().canonical_dict()
    dispatch["selected_participant_id"] = "driver-bad"

    with pytest.raises(RealTimeExecutionError):
        validate_real_time_execution(execution, dispatch=dispatch)
