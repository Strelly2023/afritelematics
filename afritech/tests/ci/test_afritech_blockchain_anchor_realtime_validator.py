from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_blockchain_anchor_realtime_validator as validator


def test_blockchain_anchor_realtime_validator_reports_ready() -> None:
    report = validator.validate()

    assert report.verified is True
    assert report.docs_present is True
    assert report.adr_present is True
    assert report.rule_present is True
    assert report.binding_present is True
    assert report.indexer_realtime_present is True
    assert report.api_surface_present is True
    assert report.adr_helper_present is True
    assert report.explorer_present is True
    assert report.stream_replay_present is True
    assert report.contract_link_present is True


def test_blockchain_anchor_realtime_validator_cli_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_blockchain_anchor_realtime_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASSED" in completed.stdout
