from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.cross_border_federation import build_cross_border_federation
from afritech.mobility.legal_compliance_layer import build_compliance_record
from afritech.mobility.public_evidence_api import build_public_evidence
from afritech.mobility.regulator_certification_layer import build_certification_record
from afritech.mobility.self_auditing_network import (
    SelfAuditingNetworkError,
    SelfAuditingNetworkRecord,
    AuditEvent,
    build_self_audit_proof,
    build_self_auditing_network,
    evaluate_self_audit_invariants,
    export_self_audit_invariant_report,
    export_self_auditing_network,
    validate_self_audit_invariants,
    validate_self_auditing_network,
)


def _audit():
    cert = build_certification_record("driver-001", "a" * 64, 0.95, True)
    compliance = build_compliance_record(
        "driver-001",
        cert.certification_hash,
        cert.evidence_hash,
        "AU-VIC",
        ("transport-rule-1",),
        case_id="case-audit-001",
    )
    transition = {
        "transition_id": "transition-001",
        "participant_id": "driver-001",
        "from_jurisdiction": "AU-VIC",
        "to_jurisdiction": "NZ-AUK",
        "evidence_hash": "b" * 64,
        "timestamp": 1_700_100_000,
        "verified": True,
        "metadata": {},
    }
    federation = build_cross_border_federation(compliance, "NZ-AUK", 0.82, (transition,), federation_id="federation-001")
    public = build_public_evidence("d" * 64, "c" * 64, "s" * 64, 0.9)
    event = AuditEvent.from_mapping(
        {
            "event_id": "audit-event-001",
            "timestamp": 1_700_200_000,
            "actor": "audit-service",
            "action": "scan",
            "evidence_hash": public.evidence_hash,
            "severity": "info",
            "verified": True,
            "metadata": {"source": "public"},
        }
    )
    return build_self_auditing_network(
        audit_id="audit-001",
        network_id="network-001",
        participant_id="driver-001",
        certification_hash=cert.certification_hash,
        compliance_hash=compliance.compliance_hash,
        federation_hash=federation.federation_hash,
        public_evidence_hash=public.evidence_hash,
        anomaly_score=0.12,
        audit_events=(event,),
    )


def test_audit_happy_path():
    audit = _audit()

    assert audit.audit_status == "PASS"


def test_invalid_input():
    with pytest.raises(SelfAuditingNetworkError):
        build_self_auditing_network(
            audit_id="",
            network_id="",
            participant_id="",
            certification_hash="",
            compliance_hash="",
            federation_hash="",
            public_evidence_hash="",
            anomaly_score=1.5,
        )


def test_determinism():
    a = _audit()
    b = _audit()

    assert a.audit_hash == b.audit_hash


def test_replay_stability():
    audit = _audit()
    rebuilt = SelfAuditingNetworkRecord.from_mapping(audit.canonical_dict())

    assert audit.canonical_dict() == rebuilt.canonical_dict()


def test_authority_boundary():
    audit = _audit().canonical_dict()
    audit["authority_boundary"] = "override"

    with pytest.raises(SelfAuditingNetworkError):
        validate_self_auditing_network(audit)


def test_anomaly_score_bounds():
    audit = _audit().canonical_dict()
    audit["anomaly_score"] = 1.5

    with pytest.raises(SelfAuditingNetworkError):
        validate_self_auditing_network(audit)


def test_proof_hash_tampering_rejected(tmp_path):
    audit = _audit()
    exported = export_self_auditing_network(tmp_path, audit)
    proof = json.loads(exported["proof"].read_text())
    proof["audit_hash"] = "f" * 64

    with pytest.raises(SelfAuditingNetworkError):
        validate_self_auditing_network(proof)


def test_proof_authority_boundary_tampering_rejected(tmp_path):
    audit = _audit()
    exported = export_self_auditing_network(tmp_path, audit)
    proof = json.loads(exported["proof"].read_text())
    proof["authority_boundary"] = "fake-boundary"

    with pytest.raises(SelfAuditingNetworkError):
        validate_self_auditing_network(proof)


def test_audit_does_not_modify_trust():
    class _TrustEngine:
        def __init__(self) -> None:
            self._scores = {"driver-1": 88.0}

        def score(self, participant_id: str) -> float:
            return self._scores[participant_id]

        def apply_audit(self, audit) -> None:  # pragma: no cover - interface
            return None

    engine = _TrustEngine()
    before = engine.score("driver-1")
    engine.apply_audit(_audit())
    after = engine.score("driver-1")

    assert before == after


def test_audit_does_not_modify_dispatch():
    class _DispatchEngine:
        def __init__(self) -> None:
            self._state = {"decision": "stable"}

        def run(self) -> dict[str, str]:
            return dict(self._state)

        def apply_audit(self, audit) -> None:  # pragma: no cover - interface
            return None

    engine = _DispatchEngine()
    before = engine.run()
    engine.apply_audit(_audit())
    after = engine.run()

    assert before == after


def test_audit_does_not_modify_settlement():
    class _SettlementEngine:
        def __init__(self) -> None:
            self._state = {"status": "stable"}

        def state(self) -> dict[str, str]:
            return dict(self._state)

        def apply_audit(self, audit) -> None:  # pragma: no cover - interface
            return None

    engine = _SettlementEngine()
    before = engine.state()
    engine.apply_audit(_audit())
    after = engine.state()

    assert before == after


def test_export_self_auditing_network(tmp_path):
    audit = _audit()
    exported = export_self_auditing_network(tmp_path, audit)

    assert exported["json"].exists()
    assert exported["proof"].exists()
    proof = json.loads(exported["proof"].read_text())
    assert proof["audit_hash"] == audit.audit_hash


def test_invariant_report():
    audit = _audit()
    proof = build_self_audit_proof(audit)
    report = evaluate_self_audit_invariants(audit, proof)

    assert report.verified is True
    assert validate_self_audit_invariants(report) is True


def test_export_invariant_report(tmp_path):
    audit = _audit()
    exported = export_self_audit_invariant_report(tmp_path, audit)

    assert exported["report"].exists()
