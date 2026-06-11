from __future__ import annotations

import subprocess
import sys

from afritech.ci.afriprog_afriprogramming_boundary_validator import (
    VALIDATOR_NAME,
    validate_afriprog_afriprogramming_boundary,
)


def test_boundary_validator_passes_directly() -> None:
    validate_afriprog_afriprogramming_boundary()


def test_boundary_validator_module_entrypoint_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", VALIDATOR_NAME],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout
