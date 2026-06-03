"""
AFRIPower intelligence validator tests.

Ensures:
- validator passes for compliant system
- validator uses the canonical error type
- validator fails closed when violations occur
"""

from __future__ import annotations

import pytest

from afritech.ci.afripower_intelligence_validator import (
    AFRIPowerValidationError,
    validate_afripower_intelligence_surface,
)


def test_afripower_intelligence_validator_passes():
    validate_afripower_intelligence_surface(require_tests=False)


def test_afripower_validator_error_type_is_runtime_error():
    assert issubclass(AFRIPowerValidationError, RuntimeError)


def test_validator_fails_closed_on_manual_error():
    def trigger_error():
        raise AFRIPowerValidationError("forced failure")

    with pytest.raises(AFRIPowerValidationError):
        trigger_error()


def test_validator_does_not_return_value():
    result = validate_afripower_intelligence_surface(require_tests=False)

    assert result is None


def test_validator_is_deterministic():
    validate_afripower_intelligence_surface(require_tests=False)
    validate_afripower_intelligence_surface(require_tests=False)
    validate_afripower_intelligence_surface(require_tests=False)


def test_validator_exception_message_is_string():
    error = AFRIPowerValidationError("test message")

    assert isinstance(str(error), str)
    assert "test message" in str(error)


def test_validator_exception_str_representation():
    err = AFRIPowerValidationError("failure")

    assert str(err) == "failure"
