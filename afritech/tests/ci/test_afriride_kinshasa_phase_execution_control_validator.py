"""Tests for the AfriRide Kinshasa phase execution control validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_kinshasa_phase_execution_control_validator import (
    CONTRACT_DOC,
    AfriRideKinshasaPhaseExecutionControlValidationError,
    validate_contract,
)


def test_kinshasa_phase_execution_control_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.location == "Kinshasa"
    assert report.phase_ready_to_run is True
    assert report.phase_passed_claimed is False


def test_kinshasa_phase_locks_e1_to_f3_order() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "E1 -> E2 -> E3 -> F1 -> F2 -> F3" in text
    assert "E1: deterministic_isolation_under_concurrency" in text
    assert "F3: availability_state_determinism_under_toggle_abuse" in text


def test_kinshasa_phase_locks_adversarial_hard_stops() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "race_condition" in text
    assert "dual_acceptance" in text
    assert "invalid_lifecycle_completion" in text
    assert "timing_based_selection_bias" in text


def test_kinshasa_phase_preserves_behavioral_chaos_law() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "User behavior MAY be unpredictable" in text
    assert "System output MUST remain deterministic" in text
    assert "operator_law: system_correct_despite_uncontrolled_users" in text
    assert "phase_passed_claimed: false" in text


def test_kinshasa_phase_rejects_pass_claim(tmp_path) -> None:
    altered = tmp_path / "kinshasa.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("phase_passed_claimed: false", "phase_passed_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideKinshasaPhaseExecutionControlValidationError,
        match="not verified",
    ):
        validate_contract(altered)
