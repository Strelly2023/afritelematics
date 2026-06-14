from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.public_evidence_api import build_public_evidence
from afritech.mobility.regulator_certification_layer import (
    RegulatorCertificationError,
    RegulatorCertificationRecord,
    build_certification_proof,
    build_certification_record,
    evaluate_regulator_invariants,
    export_certification,
    export_certification_invariant_report,
    validate_regulator_certification,
    validate_regulator_invariants,
)


def _cert():
    return build_certification_record("driver-001", "a" * 64, 0.95, True, evidence_refs=("ref-a", "ref-b"))


def test_certification_happy_path():
    cert = _cert()

    assert cert.certified is True
    assert cert.canonical_dict()["certification_status"] == "CERTIFIED"


def test_invalid_certification_input():
    with pytest.raises(RegulatorCertificationError):
        build_certification_record("", "", 1.5, False)


def test_certification_determinism():
    a = _cert()
    b = _cert()

    assert a.certification_hash == b.certification_hash


def test_certification_replay_stability():
    cert = _cert()
    rebuilt = RegulatorCertificationRecord.from_mapping(cert.canonical_dict())

    assert cert.canonical_dict() == rebuilt.canonical_dict()


def test_regulator_cannot_override_proof():
    cert = _cert().canonical_dict()
    cert["proof_override"] = True

    assert "proof_override" in cert
    assert validate_regulator_certification(_cert()) is True


def test_regulator_cannot_override_settlement():
    cert = _cert().canonical_dict()

    assert "settlement" not in cert


def test_regulator_cannot_modify_dispatch():
    cert = _cert().canonical_dict()

    assert "dispatch" not in cert


def test_certification_requires_evidence():
    with pytest.raises(RegulatorCertificationError):
        build_certification_record("driver-1", None, 0.9, True)  # type: ignore[arg-type]


def test_evidence_hash_binding():
    cert = _cert()

    assert cert.evidence_hash == "a" * 64


def test_proof_chain_validation():
    cert = _cert()

    assert validate_regulator_certification(cert) is True


def test_invalid_proof_chain_rejected():
    cert = _cert().canonical_dict()
    cert["evidence_hash"] = "b" * 64

    with pytest.raises(RegulatorCertificationError):
        validate_regulator_certification(cert)


def test_cert_hash_tampering_detected():
    cert = _cert().canonical_dict()
    cert["certification_hash"] = "f" * 64

    with pytest.raises(RegulatorCertificationError):
        validate_regulator_certification(cert)


def test_trust_score_tampering_detected():
    cert = _cert().canonical_dict()
    cert["trust_score"] = 0.1

    with pytest.raises(RegulatorCertificationError):
        validate_regulator_certification(cert)


def test_certification_does_not_modify_trust():
    class _TrustEngine:
        def __init__(self) -> None:
            self._scores = {"driver-1": 88.0}

        def score(self, participant_id: str) -> float:
            return self._scores[participant_id]

        def apply_certification(self, certification) -> None:  # pragma: no cover - interface
            return None

    trust_engine = _TrustEngine()
    before = trust_engine.score("driver-1")
    trust_engine.apply_certification(_cert())
    after = trust_engine.score("driver-1")

    assert before == after


def test_certification_does_not_modify_settlement():
    class _SettlementEngine:
        def __init__(self) -> None:
            self._state = {"status": "stable"}

        def state(self) -> dict[str, str]:
            return dict(self._state)

        def apply_certification(self, certification) -> None:  # pragma: no cover - interface
            return None

    settlement_engine = _SettlementEngine()
    before = settlement_engine.state()
    settlement_engine.apply_certification(_cert())
    after = settlement_engine.state()

    assert before == after


def test_certification_independent_from_public_evidence():
    public = build_public_evidence("d" * 64, "c" * 64, "s" * 64, 0.9)
    cert = build_certification_record("driver-1", public.evidence_hash, 0.9, True)

    assert cert.evidence_hash == public.evidence_hash


def test_export_certification(tmp_path):
    cert = _cert()

    exported = export_certification(tmp_path, cert)

    assert exported["json"].exists()
    assert exported["proof"].exists()

    proof = json.loads(exported["proof"].read_text())

    assert proof["certification_hash"] == cert.certification_hash
    assert proof["verified"] is True


def test_certification_reproducibility():
    hashes = {
        build_certification_record("driver-1", "a" * 64, 0.9, True).certification_hash
        for _ in range(50)
    }

    assert len(hashes) == 1


def test_certification_drift_detected():
    a = build_certification_record("driver-1", "a" * 64, 0.9, True)
    b = build_certification_record("driver-1", "b" * 64, 0.9, True)

    assert a.certification_hash != b.certification_hash


def test_proof_integrity_round_trip():
    cert = _cert()
    proof = build_certification_proof(cert)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["certification_hash"] == cert.certification_hash
    assert decoded["authority_boundary"] == "regulator_certification_proof_read_only"


def test_proof_hash_tampering_rejected(tmp_path):
    cert = _cert()
    exported = export_certification(tmp_path, cert)

    proof = json.loads(exported["proof"].read_text())
    proof["certification_hash"] = "f" * 64

    with pytest.raises(RegulatorCertificationError):
        validate_regulator_certification(proof)


def test_proof_authority_boundary_tampering_rejected(tmp_path):
    cert = _cert()
    exported = export_certification(tmp_path, cert)

    proof = json.loads(exported["proof"].read_text())
    proof["authority_boundary"] = "fake-boundary"

    with pytest.raises(RegulatorCertificationError):
        validate_regulator_certification(proof)


def test_invariant_report():
    cert = _cert()
    proof = build_certification_proof(cert)
    report = evaluate_regulator_invariants(cert, proof)

    assert report.verified is True
    assert validate_regulator_invariants(report) is True


def test_export_invariant_report(tmp_path):
    cert = _cert()
    exported = export_certification_invariant_report(tmp_path, cert)

    assert exported["report"].exists()
    loaded = json.loads(exported["report"].read_text())
    assert loaded["verified"] is True
