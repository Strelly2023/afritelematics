from __future__ import annotations

import subprocess
import sys

from afritech.ci import afritech_constitutional_pillars_validator as validator


def test_constitutional_pillars_validator_reports_all_four_ga_elite_pillars():
    report = validator.validate()

    assert report.verified is True
    assert [pillar.pillar_id for pillar in report.pillars] == [
        "DETERMINISTIC_TRUTH",
        "ORCHESTRATION",
        "DATA_LOCALITY",
        "OBSERVABILITY",
    ]
    assert all(pillar.ga_elite_complete for pillar in report.pillars)


def test_constitutional_pillars_validator_cli_passes():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.ci.afritech_constitutional_pillars_validator",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriTech constitutional pillars validation PASSED" in result.stdout
