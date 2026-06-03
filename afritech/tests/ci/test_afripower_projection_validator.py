"""Tests for the AFRIPower projection validator."""

from __future__ import annotations

from afritech.ci.afripower_projection_validator import (
    validate_afripower_projection,
)


def test_afripower_projection_validator_passes() -> None:
    validate_afripower_projection()