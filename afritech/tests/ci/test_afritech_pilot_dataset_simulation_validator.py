from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_pilot_dataset_simulation_validator as validator


def test_pilot_dataset_simulation_validator_reports_airport_scenario():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["schema"] == "afritech.pilot_dataset_simulation_report.v1"
    assert data["scenario_id"] == "airport-zone-001"
    assert data["deployment_type"] == "airport"
    assert data["operation_count"] == 3
    assert data["signal_count"] == 21
    assert len(data["dataset_hash"]) == 64


def test_pilot_dataset_simulation_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_pilot_dataset_simulation_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech pilot dataset simulation validation PASSED" in result.stdout
    assert "scenario_id=airport-zone-001" in result.stdout
    assert "operations=3 signals=21" in result.stdout
