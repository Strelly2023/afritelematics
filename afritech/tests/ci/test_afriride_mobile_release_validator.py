from __future__ import annotations

import subprocess
import sys

from afritech.ci import afriride_mobile_release_validator as validator


def test_afriride_mobile_release_validator_reports_ready() -> None:
    report = validator.validate()

    assert report.verified is True
    assert report.contract_present is True
    assert report.manifests_present is True
    assert report.app_sources_present is True
    assert report.legal_docs_present is True
    assert report.api_surface_present is True
    assert report.release_gates_present is True
    assert report.authority_boundary_present is True


def test_afriride_mobile_release_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_mobile_release_validator"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PASSED" in result.stdout
