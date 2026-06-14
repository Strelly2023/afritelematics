from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_operator_decision_protocol_validator as validator


def test_operator_decision_protocol_validator_reports_ready():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["adr_id"] == "ADR-0044"
    assert data["rule_id"] == "RULE-064"
    assert data["binding_id"] == "BIND-042"


def test_operator_decision_protocol_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_operator_decision_protocol_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech operator decision protocol validation PASSED" in result.stdout
    assert "ADR-0044" in result.stdout
