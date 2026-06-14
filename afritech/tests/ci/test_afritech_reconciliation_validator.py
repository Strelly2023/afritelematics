from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_reconciliation_validator as validator


def test_reconciliation_validator_reports_airport_alignment():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["scenario_id"] == "airport-zone-001"
    assert data["deployment_type"] == "airport"
    assert data["operation_count"] == 3
    assert data["divergence_count"] == 0
    assert data["divergence_score"] == 0.0
    assert data["recommendation"] == "continue"


def test_reconciliation_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_reconciliation_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech reconciliation validation PASSED" in result.stdout
    assert "scenario_id=airport-zone-001" in result.stdout
    assert "divergence_count=0" in result.stdout
