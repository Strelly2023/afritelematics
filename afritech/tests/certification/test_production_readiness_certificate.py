from __future__ import annotations

from afritech.certification.production_readiness_certificate import (
    CERTIFICATE_CLASSIFICATION,
    REQUIRED_GATES,
    REQUIRED_LIMITATIONS,
    GateCertificateEntry,
    build_production_readiness_certificate,
)
from afritech.ci.production_readiness_certificate_validator import (
    run_production_readiness_certificate_validation,
)


def test_production_readiness_certificate_aggregates_all_gates():
    certificate = build_production_readiness_certificate()

    assert tuple(gate.gate_name for gate in certificate.gates) == REQUIRED_GATES
    assert certificate.verified is True
    assert certificate.classification == CERTIFICATE_CLASSIFICATION


def test_production_readiness_certificate_includes_required_fields():
    certificate = build_production_readiness_certificate()
    gate = certificate.gates[0]

    assert gate.status == "IMPLEMENTED"
    assert gate.validator_result == "PASSED"
    assert len(gate.replay_hash) == 64
    assert len(gate.report_hash) == 64
    assert gate.proof_timestamp == "2026-05-26T00:00:00Z"
    assert gate.remaining_limitations == REQUIRED_LIMITATIONS


def test_production_readiness_certificate_pins_explicit_limitations():
    certificate = build_production_readiness_certificate()

    assert "not globally production-proven" in certificate.remaining_limitations
    assert "not internet-scale proven" in certificate.remaining_limitations
    assert "not multi-region cloud proven" in certificate.remaining_limitations
    assert "not Byzantine-public-network proven" in certificate.remaining_limitations
    assert "not massive commercial-volume proven" in certificate.remaining_limitations
    assert "not adversarially nation-state proven" in certificate.remaining_limitations


def test_production_readiness_certificate_does_not_inflate_classification():
    inflated = GateCertificateEntry(
        bounded_classification="globally production-proven superplatform",
        gate_name="Gate 1 — Load Proof",
        proof_timestamp="2026-05-26T00:00:00Z",
        remaining_limitations=REQUIRED_LIMITATIONS,
        replay_hash="0" * 64,
        report_hash="1" * 64,
        status="IMPLEMENTED",
        validator_result="PASSED",
    )

    assert inflated.verified is False


def test_production_readiness_certificate_hash_is_deterministic():
    first = build_production_readiness_certificate()
    second = build_production_readiness_certificate()

    assert first.certificate_hash() == second.certificate_hash()


def test_production_readiness_certificate_validator_report_is_verified():
    report = run_production_readiness_certificate_validation()

    assert report.verified is True
    assert report.gate_count == len(REQUIRED_GATES)
    assert report.gate_names == REQUIRED_GATES
    assert len(report.report_hash()) == 64

