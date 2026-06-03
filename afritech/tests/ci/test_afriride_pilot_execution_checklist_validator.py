"""Tests for the AfriRide pilot execution checklist validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_pilot_execution_checklist_validator import (
    CONTRACT_DOC,
    AfriRidePilotExecutionChecklistValidationError,
    validate_contract,
)


def test_pilot_execution_checklist_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.live_pilot_ready_to_run is True
    assert report.pilot_executed_claimed is False
    assert report.no_step_skipping_allowed is True


def test_pilot_execution_checklist_locks_no_skip_rule() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Do NOT skip steps" in text
    assert "no_step_skipping_allowed: true" in text
    assert "If any pre-run check fails -> ABORT PILOT" in text


def test_pilot_execution_checklist_locks_stop_conditions() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "replay_mismatch -> STOP" in text
    assert "identity_drift -> STOP" in text
    assert "missing_event -> STOP" in text


def test_pilot_execution_checklist_preserves_truth_law() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "You are NOT validating success" in text
    assert "You are validating truth" in text
    assert "operator_law: validate_truth_not_success" in text


def test_pilot_execution_checklist_rejects_execution_claim(tmp_path) -> None:
    altered = tmp_path / "checklist.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("pilot_executed_claimed: false", "pilot_executed_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRidePilotExecutionChecklistValidationError,
        match="not verified",
    ):
        validate_contract(altered)
