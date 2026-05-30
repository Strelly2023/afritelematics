from __future__ import annotations

import pytest

from afritech.ci import afritpps_execution_validator as validator
from afritech.ci.afritpps_execution_validator import (
    AfriTPPSValidationError,
    validate_afritpps_execution_surface,
)


def test_afritpps_execution_validator_passes():
    validate_afritpps_execution_surface()


def test_afritpps_validator_fails_closed_on_bad_identity(monkeypatch):
    monkeypatch.setattr(validator, "AFRITPPS_COMPONENT", "BadTPPS")

    with pytest.raises(AfriTPPSValidationError, match="component"):
        validator.validate_identity()


def test_afritpps_validator_checks_required_tests(monkeypatch):
    monkeypatch.setattr(
        validator,
        "REQUIRED_TEST_FILES",
        (validator.AFRITPPS_TEST_ROOT / "missing.py",),
    )

    with pytest.raises(AfriTPPSValidationError, match="missing AfriTPPS test"):
        validator.validate_required_tests()
