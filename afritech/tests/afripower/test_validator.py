from __future__ import annotations

import pytest

from afritech.ci import afripower_intelligence_validator as validator
from afritech.ci.afripower_intelligence_validator import (
    AFRIPowerValidationError,
    run_validation,
    validate_afripower_intelligence_surface,
    validate_identity,
    validate_no_authority,
    validate_no_mutation,
    validate_projection_contracts,
)


def test_validator_identity_passes():
    validate_identity()


def test_validator_no_authority_passes():
    validate_no_authority()


def test_validator_no_mutation_passes():
    validate_no_mutation()


def test_validator_projection_contracts_pass():
    validate_projection_contracts()


def test_validator_surface_passes():
    validate_afripower_intelligence_surface(require_tests=False)


def test_run_validation_passes(capsys):
    result = run_validation(())

    captured = capsys.readouterr()

    assert result == 0
    assert "AFRIPower intelligence validation PASSED" in captured.out


def test_validator_fails_closed_on_authority(monkeypatch):
    monkeypatch.setattr(
        validator,
        "AUTHORITY_FLAGS",
        (("RUNTIME_AUTHORITY", True),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_no_authority()


def test_validator_fails_closed_on_mutation(monkeypatch):
    monkeypatch.setattr(
        validator,
        "MUTATION_FLAGS",
        (("MUTATION_ALLOWED", True),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_no_mutation()
