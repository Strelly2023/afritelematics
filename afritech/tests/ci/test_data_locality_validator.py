from __future__ import annotations

import subprocess
import sys

import pytest

from afritech.ci import data_locality_validator as validator


def test_data_locality_validator_accepts_ga_elite_surface():
    report = validator.validate()

    assert report.verified is True
    assert report.concept_id == "CONCEPT_DATA_LOCALITY"
    assert report.strict_guard_verified is True
    assert report.scheduler_trace_verified is True


def test_data_locality_quality_rejects_random_access():
    with pytest.raises(validator.DataLocalityValidationError, match="low locality"):
        validator.validate_locality_quality({"access_pattern": [1, 9, 2, 8, 3]})


def test_data_locality_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.data_locality_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Data Locality validation PASSED" in result.stdout
