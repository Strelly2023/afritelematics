from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_governed_evidence_protocol_validator as validator


def test_governed_evidence_protocol_validator_reports_ready() -> None:
    report = validator.validate()

    assert report.verified is True
    assert report.docs_present is True
    assert report.adr_present is True
    assert report.rule_present is True
    assert report.binding_present is True
    assert report.protocol_builder_present is True
    assert report.api_surface_present is True
    assert report.explorer_present is True
    assert report.governance_hashes_present is True
    assert report.validator_chain_present is True


def test_governed_evidence_protocol_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_governed_evidence_protocol_validator"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PASSED" in result.stdout
