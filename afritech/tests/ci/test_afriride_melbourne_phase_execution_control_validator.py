"""Tests for the AfriRide Melbourne phase execution control validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_melbourne_phase_execution_control_validator import (
    CONTRACT_DOC,
    AfriRideMelbournePhaseExecutionControlValidationError,
    validate_contract,
)


def test_melbourne_phase_execution_control_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.location == "Melbourne"
    assert report.phase_ready_to_run is True
    assert report.phase_passed_claimed is False


def test_melbourne_phase_locks_a1_to_a5_order() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "A1 -> A2 -> A3 -> A4 -> A5" in text
    assert "A1: deterministic_ride_lifecycle" in text
    assert "A5: payment_failure_state_isolation" in text


def test_melbourne_phase_locks_hard_stops() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "replay_mismatch" in text
    assert "identity_drift" in text
    assert "missing_event" in text
    assert "payment_state_corrupts_trip_state" in text


def test_melbourne_phase_preserves_replay_truth_boundary() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "lets replay decide truth" in text
    assert "manually_declare_success" in text
    assert "phase_passed_claimed: false" in text


def test_melbourne_phase_rejects_pass_claim(tmp_path) -> None:
    altered = tmp_path / "melbourne.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("phase_passed_claimed: false", "phase_passed_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideMelbournePhaseExecutionControlValidationError,
        match="not verified",
    ):
        validate_contract(altered)
