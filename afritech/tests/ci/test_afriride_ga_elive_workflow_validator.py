from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from afritech.ci import afriride_ga_elive_workflow_validator as validator


ROOT = Path(__file__).resolve().parents[3]
GA_WORKFLOW = ROOT / ".github/workflows/ga_plus_plus_plus.yml"


def test_ga_elive_workflow_validator_reports_bounded_phase5_contract() -> None:
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["schema"] == "afriride.ga_elive_workflow.v1"
    assert data["status"] == "phase_5_active"
    assert data["classification"] == "ga_elive_deterministic_mobility_workflow"
    assert data["truth_authority"] == "replay_only"
    assert data["pipeline"] == list(validator.REQUIRED_PIPELINE)
    assert data["proven_evidence"] == list(validator.PROVEN_PHASE5_EVIDENCE)
    assert data["not_yet_proven"] == list(validator.NOT_YET_PROVEN)


def test_ga_elive_workflow_preserves_execution_and_authority_boundaries() -> None:
    text = validator.WORKFLOW_DOC.read_text(encoding="utf-8")

    for phrase in (
        "No direct API-to-core execution allowed",
        "Uber-like first-accept race semantics are forbidden",
        "same declared matching input -> same driver assignment",
        "Receipts and UI summaries are derived evidence only.",
        "They must not participate in or mutate the canonical event hash chain.",
    ):
        assert phrase in text

    lowered = text.lower()
    for forbidden in validator.FORBIDDEN_CLAIMS:
        assert forbidden not in lowered


def test_ga_elive_workflow_validator_summary_is_precise() -> None:
    summary = validator.format_summary(validator.validate())

    assert "AfriRide GA eLive workflow validation PASSED" in summary
    assert "status=phase_5_active" in summary
    assert "classification=ga_elive_deterministic_mobility_workflow" in summary
    assert "pipeline_stages=15" in summary
    assert "truth_authority=replay_only" in summary
    assert "verified=True" in summary


def test_ga_elive_workflow_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_ga_elive_workflow_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriRide GA eLive workflow validation PASSED" in result.stdout
    assert "truth_authority=replay_only" in result.stdout


def test_ga_elive_validator_is_mandatory_in_main_ga_workflow() -> None:
    workflow = GA_WORKFLOW.read_text(encoding="utf-8")

    assert "Validate AfriRide GA eLive workflow contract" in workflow
    assert "python3 -m afritech.ci.afriride_ga_elive_workflow_validator" in workflow
    assert workflow.index("python3 -m afritech.ci.mobile_pilot_e2e_validator") < workflow.index(
        "python3 -m afritech.ci.afriride_ga_elive_workflow_validator"
    )
    assert workflow.index("python3 -m afritech.ci.marketplace_simulation_validator") < workflow.index(
        "python3 -m afritech.ci.afriride_ga_elive_workflow_validator"
    )
