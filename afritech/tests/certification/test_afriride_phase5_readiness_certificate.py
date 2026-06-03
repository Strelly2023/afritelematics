from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from afritech.certification.afriride_phase5_readiness_certificate import (
    CERTIFICATE_CLASSIFICATION,
    REMAINING_GAPS,
    REQUIRED_EVIDENCE,
    AfriRidePhase5ReadinessCertificate,
    Phase5EvidenceEntry,
    build_afriride_phase5_readiness_certificate,
)
from afritech.ci.afriride_phase5_readiness_certificate_validator import (
    run_afriride_phase5_readiness_certificate_validation,
)


ROOT = Path(__file__).resolve().parents[3]
CERTIFICATE_DOC = ROOT / "docs/proof/AFRIRIDE_PHASE5_READINESS_CERTIFICATE.md"
GA_WORKFLOW = ROOT / ".github/workflows/ga_plus_plus_plus.yml"


def test_phase5_readiness_certificate_aggregates_required_evidence() -> None:
    certificate = build_afriride_phase5_readiness_certificate()

    assert tuple(entry.evidence_name for entry in certificate.evidence) == REQUIRED_EVIDENCE
    assert certificate.verified is True
    assert certificate.classification == CERTIFICATE_CLASSIFICATION
    assert certificate.truth_authority == "replay_only"
    assert certificate.write_enabled is False
    assert certificate.mutation_authority is False


def test_phase5_readiness_certificate_pins_remaining_gaps() -> None:
    certificate = build_afriride_phase5_readiness_certificate()

    assert certificate.remaining_gaps == REMAINING_GAPS
    for gap in (
        "real Flutter driver app to running backend to real rider app not yet proven",
        "multi-driver contention not yet proven",
        "network interruption recovery not yet proven",
        "pilot field operation not yet proven",
        "production key custody not yet proven",
    ):
        assert gap in certificate.remaining_gaps


def test_phase5_readiness_certificate_evidence_entries_are_hash_bound() -> None:
    certificate = build_afriride_phase5_readiness_certificate()

    for entry in certificate.evidence:
        assert entry.status == "PASSED"
        assert entry.authority == "bounded_evidence_only"
        assert len(entry.evidence_hash) == 64
        assert entry.files
        assert entry.commands
        assert entry.verified is True


def test_phase5_readiness_certificate_rejects_inflated_authority() -> None:
    entry = build_afriride_phase5_readiness_certificate().evidence[0]
    inflated = AfriRidePhase5ReadinessCertificate(
        evidence=(entry,),
        classification="controlled pilot ready and public launch approved",
        remaining_gaps=(),
        write_enabled=True,
        mutation_authority=True,
        truth_authority="certificate_declared_truth",
    )

    assert inflated.verified is False


def test_phase5_readiness_evidence_entry_rejects_wrong_status() -> None:
    entry = Phase5EvidenceEntry(
        commands=("pytest -q afriride_system/tests/e2e/test_live_local_mobile_clients_e2e.py",),
        evidence_hash="0" * 64,
        evidence_name="Live/local rider-backend-driver E2E",
        files=("afriride_system/tests/e2e/test_live_local_mobile_clients_e2e.py",),
        status="CLAIMED",
    )

    assert entry.verified is False


def test_phase5_readiness_certificate_hash_is_deterministic() -> None:
    first = build_afriride_phase5_readiness_certificate()
    second = build_afriride_phase5_readiness_certificate()

    assert first.certificate_hash() == second.certificate_hash()


def test_phase5_readiness_certificate_validator_report_is_verified() -> None:
    report = run_afriride_phase5_readiness_certificate_validation()

    assert report.verified is True
    assert report.evidence_count == len(REQUIRED_EVIDENCE)
    assert report.evidence_names == REQUIRED_EVIDENCE
    assert report.remaining_gaps == REMAINING_GAPS
    assert len(report.report_hash()) == 64


def test_phase5_readiness_certificate_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_phase5_readiness_certificate_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriRide Phase 5 readiness certificate validation PASSED" in result.stdout
    assert "truth_authority=replay_only" in result.stdout


def test_phase5_readiness_certificate_doc_preserves_non_claims() -> None:
    text = CERTIFICATE_DOC.read_text(encoding="utf-8")

    assert "STATUS: PHASE 5 READINESS CERTIFICATE" in text
    assert "truth_authority: replay_only" in text
    assert "write_enabled: false" in text
    assert "mutation_authority: false" in text
    assert "The certificate is not a source of truth." in text
    for gap in REMAINING_GAPS:
        assert gap in text


def test_phase5_readiness_certificate_is_mandatory_in_main_ga_workflow() -> None:
    workflow = GA_WORKFLOW.read_text(encoding="utf-8")

    assert "Validate AfriRide Phase 5 readiness certificate" in workflow
    assert "python3 -m afritech.ci.afriride_phase5_readiness_certificate_validator" in workflow
    assert workflow.index("python3 -m afritech.ci.afriride_ga_elive_workflow_validator") < workflow.index(
        "python3 -m afritech.ci.afriride_phase5_readiness_certificate_validator"
    )
