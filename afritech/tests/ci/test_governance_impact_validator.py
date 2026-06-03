"""Tests for the Governance Impact validator."""

from __future__ import annotations

from afritech.ci.governance_impact_validator import (
    validate_governance_impact,
)


def test_governance_impact_validator_passes() -> None:
    validate_governance_impact()