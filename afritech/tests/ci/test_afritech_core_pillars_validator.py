from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_core_pillars_validator as validator


def test_core_pillars_validator_reports_five_layers_and_eighteen_pillars():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["layer_count"] == 5
    assert data["pillar_count"] == 18
    assert [layer.layer_id for layer in report.layers] == [
        "CONSTITUTIONAL_KERNEL",
        "RUNTIME",
        "DISTRIBUTED_SCALE",
        "GOVERNANCE",
        "HUMAN_ECOSYSTEM",
    ]
    assert report.layers[0].pillars[0].name == "Deterministic Execution"
    assert report.layers[-1].pillars[-1].name == "Infrastructure Sovereignty"


def test_core_pillars_format_summary_contains_mature_structure():
    report = validator.validate()
    summary = validator.format_summary(report)

    assert "AfriTech core pillars validation PASSED" in summary
    assert "Constitutional Kernel" in summary
    assert "Runtime and Operational" in summary
    assert "Distributed Scale" in summary
    assert "Governance and Proof" in summary
    assert "Human and Ecosystem" in summary
    assert "Deterministic Execution" in summary
    assert "Infrastructure Sovereignty" in summary


def test_core_pillars_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_core_pillars_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "layer_count=5 pillar_count=18" in result.stdout
    assert "Data Locality: Compute near the data." in result.stdout
