"""Tests for the AfriRide global validation phase execution control validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_global_validation_phase_execution_control_validator import (
    CONTRACT_DOC,
    AfriRideGlobalValidationPhaseExecutionControlValidationError,
    validate_contract,
)


def test_global_validation_phase_execution_control_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.phase_ready_to_run is True
    assert report.phase_passed_claimed is False


def test_global_validation_phase_locks_g1_to_g3_order() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "G1 -> G2 -> G3" in text
    assert "G1: global_replay_integrity" in text
    assert "G3: global_event_completeness" in text


def test_global_validation_phase_locks_all_regions_and_scenarios() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Melbourne" in text
    assert "Bujumbura_Uvira" in text
    assert "Kinshasa" in text
    assert "A1" in text
    assert "F3" in text


def test_global_validation_phase_preserves_system_truth_law() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Truth MUST remain consistent across ALL regions for ALL scenarios" in text
    assert "operator_law: all_regions_form_one_consistent_truth_system" in text
    assert "phase_passed_claimed: false" in text


def test_global_validation_phase_rejects_pass_claim(tmp_path) -> None:
    altered = tmp_path / "global.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("phase_passed_claimed: false", "phase_passed_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideGlobalValidationPhaseExecutionControlValidationError,
        match="not verified",
    ):
        validate_contract(altered)
