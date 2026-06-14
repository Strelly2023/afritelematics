from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_trusted_scale_infrastructure_validator as validator


def test_trusted_scale_infrastructure_validator_reports_authority_and_bindings():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["authority_chain"] == (
        "Constitution",
        "Deterministic Truth",
        "Replay",
        "Proof",
    )
    assert data["adr_id"] == "ADR-0042"
    assert data["rule_id"] == "RULE-062"
    assert data["binding_id"] == "BIND-040"
    assert data["runbook"] == "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md"
    assert set(data["required_bindings"]) == {
        "dispatch_id",
        "operation_id",
        "selected_participant_id",
        "event_sequence_id",
        "evidence_hash",
        "captured_at",
    }
    assert "field_evidence_as_truth_authority" in data["forbidden"]
    assert "field_evidence_overrides_replay" in data["forbidden"]


def test_trusted_scale_infrastructure_summary_contains_runbook_and_chain():
    report = validator.validate()
    summary = validator.format_summary(report)

    assert "AfriTech trusted-scale infrastructure validation PASSED" in summary
    assert "authority_chain=Constitution -> Deterministic Truth -> Replay -> Proof" in summary
    assert "adr=ADR-0042 rule=RULE-062 binding=BIND-040" in summary
    assert "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md" in summary


def test_trusted_scale_infrastructure_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_trusted_scale_infrastructure_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech trusted-scale infrastructure validation PASSED" in result.stdout
    assert "authority_chain=Constitution -> Deterministic Truth -> Replay -> Proof" in result.stdout
