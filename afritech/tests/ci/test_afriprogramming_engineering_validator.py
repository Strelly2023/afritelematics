from __future__ import annotations

import subprocess
import sys

from afritech.ci import afriprogramming_engineering_validator as validator


def test_validate_afriprogramming_engineering_surface():
    validator.validate_afriprogramming_engineering_surface()


def test_afriprogramming_engineering_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", validator.VALIDATOR_NAME],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AfriProgramming engineering validation PASSED" in result.stdout
