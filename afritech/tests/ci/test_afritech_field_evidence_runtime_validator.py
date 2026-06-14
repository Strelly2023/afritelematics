from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_field_evidence_runtime_validator as validator


def test_field_evidence_runtime_validator_reports_first_signal_flow():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["schema"] == "afritech.field_evidence_runtime_report.v1"
    assert data["signal_count"] == 7
    assert data["event_count"] == 7
    assert data["authority_boundary"] == "field_evidence_ingestion_read_only"
    assert len(data["collection_hash"]) == 64
    assert len(data["proof_hash"]) == 64
    assert len(data["ingestion_hash"]) == 64


def test_field_evidence_runtime_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_field_evidence_runtime_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech field evidence runtime validation PASSED" in result.stdout
    assert "signals=7" in result.stdout
    assert "events=7" in result.stdout
    assert "ingestion_hash=" in result.stdout
