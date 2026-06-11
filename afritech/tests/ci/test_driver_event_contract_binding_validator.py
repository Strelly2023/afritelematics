from __future__ import annotations

import subprocess
import sys

from afritech.ci import driver_event_contract_binding_validator as validator


def test_driver_event_contract_binding_validator_passes():
    assert validator.validate() is True


def test_driver_event_contract_binding_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.driver_event_contract_binding_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Driver event contract binding validation PASSED" in result.stdout
