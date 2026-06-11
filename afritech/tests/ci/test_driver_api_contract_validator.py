from __future__ import annotations

import subprocess
import sys

from afritech.ci import driver_api_contract_validator as validator


def test_driver_api_contract_validator_passes():
    assert validator.validate() is True


def test_driver_api_contract_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.driver_api_contract_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Driver API contract validation PASSED" in result.stdout


def test_driver_api_contract_validator_explain_lists_valid_and_invalid_routes():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.ci.driver_api_contract_validator",
            "--explain",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "✅ POST /driver/availability" in result.stdout
    assert "❌ POST /api/driver/availability/ -> 404" in result.stdout
