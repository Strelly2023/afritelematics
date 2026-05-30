from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_eight_pillars_validator as validator


def test_eight_pillars_validator_reports_constitutional_and_ecosystem_summaries():
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["pillar_count"] == 8
    assert data["constitutional_pillar_count"] == 4
    assert data["ecosystem_pillar_count"] == 4
    assert [pillar.pillar_id for pillar in report.constitutional_pillars] == [
        "DETERMINISTIC_TRUTH",
        "ORCHESTRATION",
        "DATA_LOCALITY",
        "OBSERVABILITY",
    ]
    assert [pillar.pillar_id for pillar in report.ecosystem_pillars] == [
        "AfriCPPT",
        "AfriTPPS",
        "AfriProgramming",
        "AFRIPower",
    ]
    assert all(pillar.summary for pillar in report.pillars)
    assert all(pillar.outputs for pillar in report.pillars)


def test_eight_pillars_format_summary_contains_all_pillars():
    report = validator.validate()
    summary = validator.format_summary(report)

    assert "AfriTech eight pillars validation PASSED" in summary
    for expected in (
        "Deterministic Truth",
        "Orchestration",
        "Data Locality",
        "Observability",
        "AfriCPPT",
        "AfriTPPS",
        "AfriProgramming",
        "AFRIPower",
    ):
        assert expected in summary


def test_eight_pillars_validator_cli_passes_and_prints_summaries():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afritech_eight_pillars_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pillar_count=8 verified=True" in result.stdout
    assert "CONSTITUTIONAL: Deterministic Truth" in result.stdout
    assert "ECOSYSTEM: AFRIPower" in result.stdout
