from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.cross_border_federation import (
    CrossBorderFederationError,
    CrossBorderFederationRecord,
    CrossBorderTransition,
    build_cross_border_federation,
    build_cross_border_proof,
    evaluate_cross_border_invariants,
    export_cross_border_federation,
    export_cross_border_invariant_report,
    validate_cross_border_federation,
    validate_cross_border_invariants,
)
from afritech.mobility.legal_compliance_layer import build_compliance_record
from afritech.mobility.regulator_certification_layer import build_certification_record


def _federation():
    cert = build_certification_record("driver-001", "a" * 64, 0.95, True)
    compliance = build_compliance_record(
        "driver-001",
        cert.certification_hash,
        cert.evidence_hash,
        "AU-VIC",
        ("transport-rule-1",),
        case_id="case-border-001",
    )
    transition = CrossBorderTransition.from_mapping(
        {
            "transition_id": "transition-001",
            "participant_id": "driver-001",
            "from_jurisdiction": "AU-VIC",
            "to_jurisdiction": "NZ-AUK",
            "evidence_hash": "b" * 64,
            "timestamp": 1_700_100_000,
            "verified": True,
            "metadata": {},
        }
    )
    return build_cross_border_federation(compliance, "NZ-AUK", 0.82, (transition,), federation_id="federation-001")


def test_federation_happy_path():
    federation = _federation()

    assert federation.federation_status == "CLEARED"


def test_invalid_membership():
    cert = build_certification_record("driver-001", "a" * 64, 0.95, True)
    compliance = build_compliance_record(
        "driver-001",
        cert.certification_hash,
        cert.evidence_hash,
        "AU-VIC",
        ("transport-rule-1",),
        case_id="case-border-001",
    )

    with pytest.raises(CrossBorderFederationError):
        build_cross_border_federation(compliance, "AU-VIC", 0.82, ())


def test_identity_uniqueness():
    federation = _federation()
    duplicated = deepcopy(federation.canonical_dict())
    duplicated["border_transitions"].append(deepcopy(duplicated["border_transitions"][0]))

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(duplicated)


def test_trust_transfer_bounded():
    federation = _federation()

    assert 0.0 <= federation.trust_score <= 1.0


def test_cross_border_trust_replay():
    federation = _federation()
    replay = CrossBorderFederationRecord.from_mapping(federation.canonical_dict())

    assert federation.federation_hash == replay.federation_hash
    assert federation.canonical_dict() == replay.canonical_dict()


def test_cross_network_custody_chain():
    federation = _federation()

    assert federation.from_jurisdiction == "AU-VIC"
    assert federation.to_jurisdiction == "NZ-AUK"


def test_multi_network_handoff_integrity():
    federation = _federation()

    assert len(federation.border_transitions) == 1
    assert federation.border_transitions[0].from_jurisdiction == "AU-VIC"


def test_duplicate_identity_rejected():
    federation = _federation().canonical_dict()
    federation["participant_id"] = " "

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(federation)


def test_unverified_network_rejected():
    federation = _federation().canonical_dict()
    federation["verified"] = False

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(federation)


def test_trust_inflation_blocked():
    federation = _federation().canonical_dict()
    federation["trust_score"] = 1.5

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(federation)


def test_proof_integrity_round_trip():
    federation = _federation()
    proof = build_cross_border_proof(federation)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["federation_hash"] == federation.federation_hash
    assert decoded["authority_boundary"] == "cross_border_federation_proof_read_only"


def test_proof_hash_tampering_rejected(tmp_path):
    federation = _federation()
    exported = export_cross_border_federation(tmp_path, federation)
    proof = json.loads(exported["proof"].read_text())
    proof["federation_hash"] = "f" * 64

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(proof)


def test_proof_authority_boundary_tampering_rejected(tmp_path):
    federation = _federation()
    exported = export_cross_border_federation(tmp_path, federation)
    proof = json.loads(exported["proof"].read_text())
    proof["authority_boundary"] = "fake-boundary"

    with pytest.raises(CrossBorderFederationError):
        validate_cross_border_federation(proof)


def test_export_cross_border(tmp_path):
    federation = _federation()
    exported = export_cross_border_federation(tmp_path, federation)

    assert exported["json"].exists()
    assert exported["proof"].exists()

    proof = json.loads(exported["proof"].read_text())
    assert proof["federation_hash"] == federation.federation_hash


def test_invariant_report():
    federation = _federation()
    proof = build_cross_border_proof(federation)
    report = evaluate_cross_border_invariants(federation, proof)

    assert report.verified is True
    assert validate_cross_border_invariants(report) is True


def test_export_invariant_report(tmp_path):
    federation = _federation()
    exported = export_cross_border_invariant_report(tmp_path, federation)

    assert exported["report"].exists()
