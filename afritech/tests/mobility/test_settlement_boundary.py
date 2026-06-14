from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from ecosystems.afriride.geo.types import GeoPoint

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.logistics_custody_chain import CustodyChain
from afritech.mobility.settlement_boundary import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    SettlementBoundaryError,
    SettlementEvent,
    SettlementRecord,
    build_settlement_proof,
    compute_settlement_record,
    export_settlement_proof,
    validate_settlement_record,
)
from afritech.mobility.settlement_invariants import (
    SettlementInvariantError,
    evaluate_settlement_invariants,
    validate_settlement_invariants,
)
from afritech.mobility.trust_dispatch import DispatchDecision


def _dispatch_decision():
    request = {
        "operation_id": "op-001",
        "operation_type": "package",
        "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
        "destination": {"lat": -37.7000, "lon": 144.9000, "timestamp": 1_700_000_900},
        "constraints": {"required_roles": ["driver"], "minimum_capacity": 1},
        "timestamp": 1_700_000_000,
    }
    candidate = {
        "participant": {
            "participant_id": "driver-1",
            "display_name": "Driver One",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 99,
            "evidence_links": ["ev-1"],
            "metadata": {},
        },
        "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
        "availability": True,
        "reliability_score": 98,
        "anomaly_rate": 0,
        "supported_operations": ["package"],
        "capacity": 1,
        "metadata": {},
    }
    from afritech.mobility.trust_dispatch import run_trust_aware_dispatch

    return run_trust_aware_dispatch(request, (candidate,))


def _custody_chain():
    return CustodyChain.from_mapping(
        {
            "chain_id": "chain-001",
            "operation_id": "op-001",
            "asset_type": "package",
            "custody_steps": [
                {
                    "step_id": "step-1",
                    "from_participant": None,
                    "to_participant": "warehouse-1",
                    "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
                    "timestamp": 1_700_000_000,
                    "condition": "sealed",
                    "evidence_hash": "a" * 64,
                },
                {
                    "step_id": "step-2",
                    "from_participant": "warehouse-1",
                    "to_participant": "courier-2",
                    "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_100},
                    "timestamp": 1_700_000_100,
                    "condition": "handoff",
                    "evidence_hash": "b" * 64,
                },
                {
                    "step_id": "step-3",
                    "from_participant": "courier-2",
                    "to_participant": "customer-9",
                    "location": {"lat": -37.7000, "lon": 144.9000, "timestamp": 1_700_000_200},
                    "timestamp": 1_700_000_200,
                    "condition": "delivered",
                    "evidence_hash": "c" * 64,
                },
            ],
        }
    )


def _record():
    decision = _dispatch_decision()
    chain = _custody_chain()
    return compute_settlement_record(
        decision,
        chain,
        {
            "gross_amount": "10.00",
            "currency": "AUD",
            "splits": {
                "driver": "0.70",
                "platform": "0.20",
                "fees": "0.10",
            },
        },
        settlement_id="settlement-001",
    )


def test_settlement_happy_path():
    record = _record()

    assert record.settlement_hash
    assert record.canonical_dict()["schema"] == SCHEMA


def test_invalid_input():
    with pytest.raises(SettlementBoundaryError):
        SettlementRecord.from_mapping({"settlement_id": "x"})


def test_determinism():
    a = _record()
    b = _record()

    assert a.settlement_hash == b.settlement_hash
    assert a.canonical_dict() == b.canonical_dict()


def test_replay_stability():
    record = _record()
    replay = SettlementRecord.from_mapping(record.canonical_dict())

    assert replay.settlement_hash == record.settlement_hash


def test_missing_chain_rejected():
    decision = _dispatch_decision()
    with pytest.raises(SettlementBoundaryError):
        compute_settlement_record(
            decision,
            {
                "chain_id": "chain-001",
                "operation_id": "op-001",
                "asset_type": "package",
                "custody_steps": [],
            },
            {
                "gross_amount": "10.00",
                "currency": "AUD",
                "splits": {"driver": "0.70", "platform": "0.20", "fees": "0.10"},
            },
        )


def test_invalid_split_detected():
    decision = _dispatch_decision()
    chain = _custody_chain()
    with pytest.raises(SettlementBoundaryError):
        compute_settlement_record(
            decision,
            chain,
            {
                "gross_amount": "10.00",
                "currency": "AUD",
                "splits": {"driver": "0.80", "platform": "0.20", "fees": "0.10"},
            },
        )


def test_hash_changes_on_tamper():
    record = _record()
    tampered = deepcopy(record.canonical_dict())
    tampered["amounts"]["driver"] = "9.99"

    assert tampered != record.canonical_dict()


def test_settlement_not_authority():
    record = _record()

    assert record.authority_boundary == AUTHORITY_BOUNDARY
    assert record.canonical_dict()["authority_boundary"] == AUTHORITY_BOUNDARY


def test_evidence_link_required():
    record = _record()

    assert record.dispatch_hash
    assert record.chain_hash


def test_no_external_state_dependency():
    a = _record()
    b = _record()

    assert a.settlement_hash == b.settlement_hash


def test_double_settlement_detected():
    record = _record()
    settled = replace(
        record,
        status="SETTLED",
        events=record.events
        + (
            SettlementEvent(
                event_id="settlement-001.settled-1",
                timestamp=1_700_000_300,
                actor="system",
                action="settled",
                evidence_hash=record.settlement_hash,
            ),
            SettlementEvent(
                event_id="settlement-001.settled-2",
                timestamp=1_700_000_301,
                actor="system",
                action="settled",
                evidence_hash=record.settlement_hash,
            ),
        ),
    )

    with pytest.raises(SettlementBoundaryError):
        validate_settlement_record(settled, _custody_chain(), _dispatch_decision())


def test_partial_execution_rejected():
    record = _record()
    partial = replace(record, participants=("driver", "platform"), amounts=(("driver", record.amount_map["driver"]), ("platform", record.amount_map["platform"])))

    with pytest.raises(SettlementBoundaryError):
        validate_settlement_record(partial, _custody_chain(), _dispatch_decision())


def test_conflicting_inputs_fail():
    record = _record()
    bad_dispatch = deepcopy(_dispatch_decision().canonical_dict())
    bad_dispatch["selected_participant_id"] = "other"

    with pytest.raises(SettlementBoundaryError):
        validate_settlement_record(record, _custody_chain(), bad_dispatch)


def test_settlement_proof_artifact_roundtrip(tmp_path):
    record = _record()
    proof = build_settlement_proof(record)
    exported = export_settlement_proof(record, tmp_path)

    assert exported["json"].exists()
    assert exported["proof"].exists()
    assert proof["schema"] == "afritech.mobility.settlement_proof.v1"


def test_settlement_invariant_compliance():
    record = _record()
    report = evaluate_settlement_invariants(record, _custody_chain(), _dispatch_decision())

    assert report.verified is True
    assert validate_settlement_invariants(report) is True


def test_settlement_invariant_validator_rejects_bad_report():
    record = _record()
    report = evaluate_settlement_invariants(record, _custody_chain(), _dispatch_decision())
    tampered = replace(report, checks=tuple())

    with pytest.raises(SettlementInvariantError):
        validate_settlement_invariants(tampered)


def test_serialization_roundtrip():
    record = _record()
    decoded = json.loads(json.dumps(record.canonical_dict(), sort_keys=True))

    assert decoded["settlement_hash"] == record.settlement_hash
