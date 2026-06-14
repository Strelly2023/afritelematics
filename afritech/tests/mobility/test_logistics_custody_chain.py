from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from ecosystems.afriride.geo.types import GeoPoint

from afritech.mobility.logistics_custody_chain import (
    AUTHORITY_BOUNDARY,
    SCHEMA,
    CustodyChain,
    LogisticsCustodyError,
    build_custody_chain_proof,
    export_custody_chain_proof,
    validate_custody_chain,
)
from afritech.mobility.logistics_custody_invariants import (
    CustodyInvariantError,
    evaluate_custody_invariants,
    validate_custody_invariants,
)


def _step(step_id: str, from_participant: str | None, to_participant: str, timestamp: int, condition: str = "handoff") -> dict[str, object]:
    return {
        "step_id": step_id,
        "from_participant": from_participant,
        "to_participant": to_participant,
        "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": timestamp},
        "timestamp": timestamp,
        "condition": condition,
        "evidence_hash": "a" * 64,
    }


def _chain() -> CustodyChain:
    return CustodyChain.from_mapping(
        {
            "chain_id": "chain-001",
            "operation_id": "op-001",
            "asset_type": "package",
            "custody_steps": [
                _step("step-1", None, "warehouse-1", 1_700_000_000, "sealed"),
                _step("step-2", "warehouse-1", "courier-2", 1_700_000_100, "handoff"),
                _step("step-3", "courier-2", "customer-9", 1_700_000_200, "received"),
            ],
        }
    )


def test_custody_chain_happy_path():
    chain = _chain()

    assert chain.chain_hash
    assert chain.canonical_dict()["schema"] == SCHEMA


def test_custody_chain_invalid_input():
    with pytest.raises(LogisticsCustodyError):
        CustodyChain.from_mapping({"chain_id": "x"})


def test_custody_chain_determinism():
    a = _chain()
    b = _chain()

    assert a.chain_hash == b.chain_hash
    assert a.canonical_dict() == b.canonical_dict()


def test_custody_chain_replay_stability():
    chain = _chain()
    replay = CustodyChain.from_mapping(chain.canonical_dict())

    assert replay.chain_hash == chain.chain_hash


def test_missing_step_detected():
    chain = _chain()
    reduced = CustodyChain(
        chain_id=chain.chain_id,
        operation_id=chain.operation_id,
        asset_type=chain.asset_type,
        custody_steps=chain.custody_steps[:-1],
    )

    with pytest.raises(LogisticsCustodyError):
        validate_custody_chain(reduced)


def test_duplicate_step_rejected():
    chain = _chain()
    duplicated = CustodyChain(
        chain_id=chain.chain_id,
        operation_id=chain.operation_id,
        asset_type=chain.asset_type,
        custody_steps=chain.custody_steps + (chain.custody_steps[0],),
    )

    with pytest.raises(LogisticsCustodyError):
        validate_custody_chain(duplicated)


def test_invalid_transition_detected():
    chain = _chain()
    invalid_steps = list(chain.custody_steps)
    invalid_steps[1] = replace(invalid_steps[1], from_participant="wrong-owner")
    invalid = CustodyChain(
        chain_id=chain.chain_id,
        operation_id=chain.operation_id,
        asset_type=chain.asset_type,
        custody_steps=tuple(invalid_steps),
    )

    with pytest.raises(LogisticsCustodyError):
        validate_custody_chain(invalid)


def test_hash_changes_on_tamper():
    chain = _chain()
    tampered = deepcopy(chain.canonical_dict())
    tampered["custody_steps"][0]["evidence_hash"] = "f" * 64

    assert tampered != chain.canonical_dict()


def test_explicit_handoff_required():
    chain = _chain()
    assert chain.custody_steps[1].from_participant == "warehouse-1"


def test_single_owner_per_step():
    chain = _chain()
    assert all(step.to_participant for step in chain.custody_steps)


def test_timestamp_order_enforced():
    chain = _chain()
    assert [step.timestamp for step in chain.custody_steps] == sorted(step.timestamp for step in chain.custody_steps)


def test_chain_break_detection():
    chain = _chain()
    broken_steps = list(chain.custody_steps)
    broken_steps[2] = replace(broken_steps[2], from_participant="unknown")
    broken = CustodyChain(
        chain_id=chain.chain_id,
        operation_id=chain.operation_id,
        asset_type=chain.asset_type,
        custody_steps=tuple(broken_steps),
    )

    with pytest.raises(LogisticsCustodyError):
        validate_custody_chain(broken)


def test_out_of_order_insertion():
    chain = _chain()
    out_of_order = CustodyChain(
        chain_id=chain.chain_id,
        operation_id=chain.operation_id,
        asset_type=chain.asset_type,
        custody_steps=(chain.custody_steps[1], chain.custody_steps[0], chain.custody_steps[2]),
    )

    with pytest.raises(LogisticsCustodyError):
        validate_custody_chain(out_of_order)


def test_evidence_corruption_detected():
    chain = _chain()
    proof = build_custody_chain_proof(chain)

    assert proof["verified"] is True
    assert proof["chain_hash"] == chain.chain_hash


def test_custody_proof_artifact_roundtrip(tmp_path):
    chain = _chain()
    proof = build_custody_chain_proof(chain)
    exported = export_custody_chain_proof(chain, tmp_path)

    assert exported["json"].exists()
    assert exported["proof"].exists()
    assert proof["schema"] == "afritech.mobility.custody_chain_proof.v1"


def test_custody_invariant_compliance():
    chain = _chain()
    report = evaluate_custody_invariants(chain)

    assert report.verified is True
    assert validate_custody_invariants(report) is True


def test_custody_invariant_validator_rejects_bad_report():
    chain = _chain()
    report = evaluate_custody_invariants(chain)
    tampered = replace(report, checks=tuple())

    with pytest.raises(CustodyInvariantError):
        validate_custody_invariants(tampered)


def test_serialization_roundtrip():
    chain = _chain()
    decoded = json.loads(json.dumps(chain.canonical_dict(), sort_keys=True))

    assert decoded["chain_hash"] == chain.chain_hash
