from __future__ import annotations

import subprocess
import sys

from afritech.ci import afriride_week_1_4_launch_validator as validator


def test_week_1_4_launch_validator_reports_real_world_scope() -> None:
    report = validator.validate()
    data = report.canonical_dict()

    assert report.verified is True
    assert data["city_count"] == 1
    assert data["driver_target"] == "10-50 active drivers"
    assert data["user_target"] == "100-300 invited users"
    assert data["weeks"] == validator.WEEKS
    assert data["minimum_product"] == validator.MINIMUM_PRODUCT
    assert data["metrics"] == validator.REALITY_METRICS
    assert data["stop_rules"] == validator.STOP_RULES


def test_week_1_4_launch_summary_is_execution_focused() -> None:
    report = validator.validate()
    summary = validator.format_summary(report)

    assert "AfriRide Week 1-4 launch validation PASSED" in summary
    assert "city_count=1" in summary
    assert "driver_target=10-50 active drivers" in summary
    assert "user_target=100-300 invited users" in summary
    assert "weeks=4" in summary
    assert "verified=True" in summary


def test_week_1_4_launch_validator_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriride_week_1_4_launch_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriRide Week 1-4 launch validation PASSED" in result.stdout
    assert "minimum_product_items=9" in result.stdout
