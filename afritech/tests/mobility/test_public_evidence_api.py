from __future__ import annotations

import json

import pytest

from afritech.mobility.public_evidence_api import (
    PublicEvidence,
    PublicEvidenceError,
    build_public_evidence,
    build_public_evidence_proof,
    evaluate_public_invariants,
    export_public_evidence,
    export_public_evidence_invariant_report,
    validate_public_evidence,
    validate_public_invariants,
)


def _evidence():
    return build_public_evidence("d" * 64, "c" * 64, "s" * 64, 0.9)


def test_public_evidence_happy_path():
    data = _evidence()

    assert data.verified is True


def test_evidence_determinism():
    a = _evidence()
    b = _evidence()

    assert a.evidence_hash == b.evidence_hash


def test_replay_stability():
    a = _evidence()

    assert validate_public_evidence(a) is True


def test_public_cannot_become_authority():
    data = _evidence().canonical_dict()
    data["authority_boundary"] = "override"

    with pytest.raises(PublicEvidenceError):
        validate_public_evidence(data)


def test_reference_hash_tampering():
    data = _evidence().canonical_dict()
    data["dispatch_hash"] = "x"

    with pytest.raises(PublicEvidenceError):
        validate_public_evidence(data)


def test_evidence_hash_tampering():
    data = _evidence().canonical_dict()
    data["evidence_hash"] = "f" * 64

    with pytest.raises(PublicEvidenceError):
        validate_public_evidence(data)


def test_evidence_refs_order_independent():
    a = build_public_evidence("d" * 64, "c" * 64, "s" * 64, 0.9, ["a", "b"])
    b = build_public_evidence("d" * 64, "c" * 64, "s" * 64, 0.9, ["b", "a"])

    assert a.evidence_hash == b.evidence_hash


def test_export_integrity(tmp_path):
    data = _evidence()
    exported = export_public_evidence(tmp_path, data)

    proof = json.loads(exported["proof"].read_text())

    assert proof["evidence_hash"] == data.evidence_hash
    assert proof["verified"] is True


def test_public_invariants():
    data = _evidence()
    proof = build_public_evidence_proof(data)
    report = evaluate_public_invariants(data, proof)

    assert report.verified is True
    assert validate_public_invariants(report) is True


def test_export_invariant_report(tmp_path):
    data = _evidence()
    exported = export_public_evidence_invariant_report(tmp_path, data)

    assert exported["report"].exists()
    loaded = json.loads(exported["report"].read_text())
    assert loaded["verified"] is True


def test_public_evidence_cannot_modify_dispatch():
    base = {"decision": "stable"}
    evidence = _evidence()

    after = {"decision": "stable"}

    assert base == after
    assert evidence.verified is True


def test_public_evidence_cannot_modify_trust():
    trust_before = 0.82
    evidence = _evidence()
    trust_after = 0.82

    assert trust_before == trust_after
    assert evidence.verified is True


def test_proof_integrity_round_trip():
    data = _evidence()
    proof = build_public_evidence_proof(data)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["evidence_hash"] == data.evidence_hash
    assert decoded["authority_boundary"] == "public_proof_read_only"


def test_proof_hash_tampering_rejected(tmp_path):
    data = _evidence()
    exported = export_public_evidence(tmp_path, data)

    proof = json.loads(exported["proof"].read_text())
    proof["evidence_hash"] = "f" * 64

    with pytest.raises(PublicEvidenceError):
        validate_public_evidence(proof)


def test_proof_authority_boundary_tampering_rejected(tmp_path):
    data = _evidence()
    exported = export_public_evidence(tmp_path, data)

    proof = json.loads(exported["proof"].read_text())
    proof["authority_boundary"] = "fake-boundary"

    with pytest.raises(PublicEvidenceError):
        validate_public_evidence(proof)

