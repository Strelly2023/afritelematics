"""Tests for the AfriTPPS execution pillar validator."""

from __future__ import annotations

import pytest

from afritech.ci.afritpps_execution_validator import (
    AfriTPPSValidationError,
    validate_afritpps_execution_surface,
    validate_identity,
)
from afritech.ci import afritpps_execution_validator as validator


def test_afritpps_execution_validator_passes():
    validate_afritpps_execution_surface()


def test_afritpps_execution_validator_fails_closed(monkeypatch):
    monkeypatch.setattr(validator, "AFRITPPS_STATUS", "INVALID_STATUS")

    with pytest.raises(AfriTPPSValidationError, match="status"):
        validate_identity()
