from __future__ import annotations

import subprocess
import sys

from afritech.ci import afriride_pilot_dominance_validator as validator


def test_pilot_dominance_validator_reports_one_city_strategy() -> None:
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["battlefield"] == "AfriRide"
    assert data["driver_range"] == "10-50"
    assert data["user_range"] == "100-300"
    assert data["positioning_line"] == "Uber guesses. We prove."
    assert data["execution_pillars"] == validator.EXECUTION_PILLARS
    assert data["dominance_loops"] == validator.DOMINANCE_LOOPS
    assert data["roadmap_stages"] == validator.ROADMAP_STAGES


def test_pilot_dominance_summary_is_product_focused() -> None:
    report = validator.validate()
    summary = validator.format_summary(report)

    assert "AfriRide pilot dominance validation PASSED" in summary
    assert "battlefield=AfriRide" in summary
    assert "drivers=10-50 users=100-300" in summary
    assert "Uber guesses. We prove." in summary
    assert "verified=True" in summary


def test_pilot_dominance_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_pilot_dominance_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriRide pilot dominance validation PASSED" in result.stdout
    assert "product_message=AfriRide is the only ride system" in result.stdout
