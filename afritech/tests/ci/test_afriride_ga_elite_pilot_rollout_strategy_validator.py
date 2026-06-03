"""Tests for the AfriRide GA Elite pilot rollout strategy validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_ga_elite_pilot_rollout_strategy_validator import (
    CONTRACT_DOC,
    AfriRideGAElitePilotRolloutStrategyValidationError,
    validate_contract,
)


def test_ga_elite_pilot_rollout_strategy_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.field_evidence_pending is True
    assert report.wave7_authorized is False


def test_rollout_strategy_preserves_evidence_first_law() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Execution -> Evidence -> Replay -> Verification -> Certification -> Expansion" in text
    assert "Expansion -> Hope -> Evidence later" in text
    assert "No claim without evidence" in text


def test_rollout_strategy_locks_phase_gates() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "min_completed_rides: 20" in text
    assert "min_completed_rides: 500" in text
    assert "min_completed_rides: 10000" in text
    assert "required_origin: field_observed" in text


def test_rollout_strategy_keeps_wave7_blocked_until_field_evidence(tmp_path) -> None:
    altered = tmp_path / "rollout.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("wave7_authorized: false", "wave7_authorized: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideGAElitePilotRolloutStrategyValidationError,
        match="not verified",
    ):
        validate_contract(altered)
