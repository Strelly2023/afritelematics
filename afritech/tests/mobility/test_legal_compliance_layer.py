from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.legal_compliance_layer import (
    LegalComplianceError,
    LegalComplianceRecord,
    build_compliance_proof,
    build_compliance_record,
    evaluate_compliance_invariants,
    export_legal_compliance,
    export_legal_compliance_invariant_report,
    validate_compliance_invariants,
    validate_legal_compliance,
)
from afritech.mobility.regulator_certification_layer import build_certification_record


def _compliance():
    cert = build_certification_record("driver-001", "a" * 64, 0.95, True)
    return build_compliance_record(
        "driver-001",
        cert.certification_hash,
        cert.evidence_hash,
        "AU-VIC",
        ("transport-rule-1", "privacy-rule-2"),
        case_id="case-legal-001",
    )


def test_legal_compliance_happy_path():
    compliance = _compliance()

    assert compliance.canonical_dict()["compliance_status"] == "COMPLIANT"


def test_invalid_input():
    with pytest.raises(LegalComplianceError):
        build_compliance_record("", "", "", "", ())


def test_determinism():
    a = _compliance()
    b = _compliance()

    assert a.compliance_hash == b.compliance_hash


def test_replay_stability():
    compliance = _compliance()
    rebuilt = LegalComplianceRecord.from_mapping(compliance.canonical_dict())

    assert compliance.canonical_dict() == rebuilt.canonical_dict()


def test_jurisdiction_explicit():
    compliance = _compliance()
    assert compliance.jurisdiction == "AU-VIC"


def test_requirements_explicit():
    compliance = _compliance()
    assert compliance.requirements == ("privacy-rule-2", "transport-rule-1")


def test_authority_boundary_not_override_proof():
    compliance = _compliance().canonical_dict()
    compliance["authority_boundary"] = "override"

    with pytest.raises(LegalComplianceError):
        validate_legal_compliance(compliance)


def test_certification_link_required():
    compliance = _compliance().canonical_dict()
    compliance["certification_hash"] = "f" * 64

    with pytest.raises(LegalComplianceError):
        validate_legal_compliance(compliance)


def test_compliance_hash_tampering_detected():
    compliance = _compliance().canonical_dict()
    compliance["compliance_hash"] = "f" * 64

    with pytest.raises(LegalComplianceError):
        validate_legal_compliance(compliance)


def test_requirements_tampering_detected():
    compliance = _compliance().canonical_dict()
    compliance["requirements"] = ["x"]

    with pytest.raises(LegalComplianceError):
        validate_legal_compliance(compliance)


def test_export_legal_compliance(tmp_path):
    compliance = _compliance()
    exported = export_legal_compliance(tmp_path, compliance)

    assert exported["json"].exists()
    assert exported["proof"].exists()
    proof = json.loads(exported["proof"].read_text())
    assert proof["compliance_hash"] == compliance.compliance_hash


def test_invariant_report():
    compliance = _compliance()
    report = evaluate_compliance_invariants(compliance)

    assert report.verified is True
    assert validate_compliance_invariants(report) is True


def test_export_invariant_report(tmp_path):
    compliance = _compliance()
    exported = export_legal_compliance_invariant_report(tmp_path, compliance)

    assert exported["report"].exists()


def test_compliance_does_not_modify_trust():
    class _TrustEngine:
        def __init__(self) -> None:
            self._scores = {"driver-1": 88.0}

        def score(self, participant_id: str) -> float:
            return self._scores[participant_id]

        def apply_compliance(self, compliance) -> None:  # pragma: no cover - interface
            return None

    engine = _TrustEngine()
    before = engine.score("driver-1")
    engine.apply_compliance(_compliance())
    after = engine.score("driver-1")

    assert before == after


def test_proof_integrity_round_trip():
    compliance = _compliance()
    proof = build_compliance_proof(compliance)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["compliance_hash"] == compliance.compliance_hash
    assert decoded["authority_boundary"] == "legal_compliance_proof_read_only"


def test_compliance_reproducibility():
    hashes = {
        build_compliance_record(
            "driver-001",
            "a" * 64,
            "b" * 64,
            "AU-VIC",
            ("transport-rule-1",),
        ).compliance_hash
        for _ in range(50)
    }

    assert len(hashes) == 1


def test_compliance_drift_detected():
    a = build_compliance_record("driver-001", "a" * 64, "b" * 64, "AU-VIC", ("transport-rule-1",))
    b = build_compliance_record("driver-001", "c" * 64, "b" * 64, "AU-VIC", ("transport-rule-1",))

    assert a.compliance_hash != b.compliance_hash

