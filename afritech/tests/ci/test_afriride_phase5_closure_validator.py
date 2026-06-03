from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from afritech.ci import afriride_phase5_closure_validator as validator


ROOT = Path(__file__).resolve().parents[3]
GA_WORKFLOW = ROOT / ".github/workflows/ga_plus_plus_plus.yml"


def test_phase5_closure_validator_reports_closed_phase_and_planned_wave6() -> None:
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["phase5_status"] == "closed"
    assert data["phase5_classification"] == "ga_plus_plus_plus_plus_phase5_readiness_certified"
    assert data["wave6_status"] == "planned"
    assert data["truth_authority"] == "replay_only"
    assert data["evidence_count"] == len(validator.EVIDENCE_CHAIN)
    assert data["transferred_gap_count"] == len(validator.TRANSFERRED_GAPS)


def test_phase5_closure_doc_preserves_constitutional_boundary() -> None:
    text = validator.PHASE5_DOC.read_text(encoding="utf-8")

    for phrase in (
        "STATUS: PHASE 5 CLOSED",
        "PHASE 5 CLOSURE DOES NOT CERTIFY CONTROLLED PILOT READINESS",
        "Capability increased.",
        "Authority did not.",
        "controlled_pilot_ready = false",
    ):
        assert phrase in text


def test_wave6_contract_remains_planned_not_ready() -> None:
    text = validator.WAVE6_DOC.read_text(encoding="utf-8")

    for phrase in (
        "STATUS: WAVE 6 PLANNED",
        "CONTROLLED PILOT READINESS CONTRACT",
        "controlled_pilot_ready: false",
        "Wave 6 may be considered complete only after:",
    ):
        assert phrase in text

    for exit_evidence in validator.WAVE6_EXIT_EVIDENCE:
        assert exit_evidence in text


def test_phase5_closure_summary_is_precise() -> None:
    summary = validator.format_summary(validator.validate())

    assert "AfriRide Phase 5 closure validation PASSED" in summary
    assert "phase5_status=closed" in summary
    assert "wave6_status=planned" in summary
    assert "truth_authority=replay_only" in summary
    assert "verified=True" in summary


def test_phase5_closure_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_phase5_closure_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriRide Phase 5 closure validation PASSED" in result.stdout
    assert "wave6_status=planned" in result.stdout


def test_phase5_closure_validator_is_mandatory_in_main_ga_workflow() -> None:
    workflow = GA_WORKFLOW.read_text(encoding="utf-8")

    assert "Validate AfriRide Phase 5 closure" in workflow
    assert "python3 -m afritech.ci.afriride_phase5_closure_validator" in workflow
    assert workflow.index(
        "python3 -m afritech.ci.afriride_phase5_readiness_certificate_validator"
    ) < workflow.index("python3 -m afritech.ci.afriride_phase5_closure_validator")
