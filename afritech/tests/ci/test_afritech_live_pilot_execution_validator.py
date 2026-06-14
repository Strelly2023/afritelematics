from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_live_pilot_execution_validator as validator


def test_live_pilot_execution_validator_reports_ready():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["checklist_doc"] == "docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md"
    assert data["ec2_test_run_doc"] == "docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md"
    assert data["operator_scenario_doc"] == "docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md"


def test_live_pilot_execution_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_live_pilot_execution_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech live pilot execution validation PASSED" in result.stdout
