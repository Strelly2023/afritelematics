from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_blockchain_anchor_validator as validator


def test_blockchain_anchor_validator_reports_ready() -> None:
    report = validator.validate()

    assert report.verified is True
    assert report.docs_present is True
    assert report.adr_present is True
    assert report.rule_present is True
    assert report.binding_present is True
    assert report.indexer_persistence_present is True
    assert report.event_subscription_present is True
    assert report.reconciliation_engine_present is True
    assert report.evidence_policy_present is True
    assert report.operational_semantics_present is True
    assert report.mainnet_gate_present is True
    assert report.multi_network_present is True
    assert report.etherscan_packet_present is True


def test_blockchain_anchor_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_blockchain_anchor_validator"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PASSED" in result.stdout
