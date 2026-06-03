from __future__ import annotations

import subprocess
import sys

from afritech.ci.afriprog_extension_validator import validate


def test_afriprog_extension_validator_accepts_current_extension():
    validate()


def test_afriprog_extension_validator_module_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.afriprog_extension_validator"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "Afriprog extension validation PASSED" in result.stdout
