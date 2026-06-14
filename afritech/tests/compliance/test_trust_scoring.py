from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import run_continuous_assurance_cycle
from afritech.compliance.continuous_assurance_invariants import validate_continuous_assurance_invariants
from afritech.compliance.continuous_assurance_threats import validate_continuous_assurance_threats
from afritech.compliance.trust_scoring import (
    TrustScoringError,
    assess_continuous_assurance_trust,
    export_trust_scoring_artifact,
    validate_continuous_assurance_trust,
)
from afritech.ci.continuous_assurance_proof_validator import validate as validate_proof


def _make_evidence_files(tmp_path: Path) -> list[Path]:
    names = (
        "cryptography_review.pdf",
        "pentest_report.pdf",
        "provider_letter.txt",
        "incident_exercise.md",
        "compliance_assessment.pdf",
    )
    paths: list[Path] = []
    for index, name in enumerate(names, start=1):
        path = tmp_path / name
        path.write_text(f"evidence-{index}:{name}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_happy_path(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.001",
    )

    invariant_report = validate_continuous_assurance_invariants(package)
    threat_report = validate_continuous_assurance_threats(package)
    proof_report = validate_proof()

    report = validate_continuous_assurance_trust(
        package,
        invariant_report=invariant_report,
        threat_report=threat_report,
        proof_report=proof_report,
    )

    assert report.verified is True
    assert report.trust_score == 100.0
    assert report.trust_grade == "MAXIMUM"
    assert report.authority_boundary == "continuous_assurance_trust_read_only"
    assert report.canonical_dict()["schema"] == "afritech.continuous_assurance_trust_report.v1"


def test_invalid_input():
    with pytest.raises(TrustScoringError, match="ContinuousAssurancePackage"):
        assess_continuous_assurance_trust(None)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_determinism(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.002",
    )
    report1 = assess_continuous_assurance_trust(package)
    report2 = assess_continuous_assurance_trust(package)

    assert report1.report_hash() == report2.report_hash()
    assert report1.canonical_dict() == report2.canonical_dict()


@pytest.mark.django_db
def test_replay_stability(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.003",
    )

    first = assess_continuous_assurance_trust(package)
    second = assess_continuous_assurance_trust(package)

    assert first.report_hash() == second.report_hash()


@pytest.mark.django_db
def test_tampering_detection(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.004",
    )
    baseline = assess_continuous_assurance_trust(package)

    tampered = deepcopy(package)
    tampered.dashboard["evidence_controls"]["provider_certification_attached"] = False

    altered = assess_continuous_assurance_trust(tampered)

    assert altered.trust_score < baseline.trust_score
    assert altered.report_hash() != baseline.report_hash()


@pytest.mark.django_db
def test_serialization_roundtrip(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.005",
    )
    report = assess_continuous_assurance_trust(package)

    encoded = json.dumps(report.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["trust_score"] == 100.0
    assert decoded["authority_boundary"] == "continuous_assurance_trust_read_only"
    assert decoded["components"][0]["name"] == "binding_integrity"


@pytest.mark.django_db
def test_schema_integrity(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.006",
    )
    report = assess_continuous_assurance_trust(package)

    assert report.canonical_dict()["schema"] == "afritech.continuous_assurance_trust_report.v1"


@pytest.mark.django_db
def test_authority_boundary(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.007",
    )
    report = assess_continuous_assurance_trust(package)

    assert report.authority_boundary == "continuous_assurance_trust_read_only"


@pytest.mark.django_db
def test_governance_constraints(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.008",
    )
    report = assess_continuous_assurance_trust(package)

    component_names = [component.name for component in report.components]

    assert component_names == [
        "binding_integrity",
        "invariant_integrity",
        "threat_detection_rate",
        "proof_validity",
        "anomaly_health",
        "evidence_completeness",
    ]
    assert pytest.approx(sum(component.weight for component in report.components), rel=0, abs=1e-9) == 1.0
    assert all(len(component.source_hash) == 64 for component in report.components)


@pytest.mark.django_db
def test_backward_compatibility(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.009",
    )
    report = assess_continuous_assurance_trust(package)

    modified = deepcopy(report.canonical_dict())
    modified.pop("authority_boundary", None)

    assert "trust_score" in modified


@pytest.mark.django_db
def test_detects_drift(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.010",
    )
    baseline = assess_continuous_assurance_trust(package)

    tampered = deepcopy(baseline.canonical_dict())
    tampered["components"][1]["score"] = 0.0

    assert tampered != baseline.canonical_dict()


@pytest.mark.django_db
def test_reproducibility_under_load(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.011",
    )

    reports = [assess_continuous_assurance_trust(package) for _ in range(5)]

    assert len(set(report.report_hash() for report in reports)) == 1


@pytest.mark.django_db
def test_proof_artifact_readiness(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.012",
    )
    report = assess_continuous_assurance_trust(package)
    export_dir = tmp_path / "exports"

    paths = export_trust_scoring_artifact(report, export_dir)

    assert paths["json"].exists()
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["verified"] is True
    assert payload["trust_grade"] == "MAXIMUM"
    assert payload["proof_report_hash"] == report.proof_report_hash


@pytest.mark.django_db
def test_validate_function_rejects_degraded_package(tmp_path: Path) -> None:
    package = run_continuous_assurance_cycle(
        evidence_items=_make_evidence_files(tmp_path),
        payment_reference="trust.score.013",
    )
    tampered = deepcopy(package)
    tampered.dashboard["evidence_controls"]["provider_certification_attached"] = False

    with pytest.raises(TrustScoringError, match="failed admission"):
        validate_continuous_assurance_trust(tampered)
