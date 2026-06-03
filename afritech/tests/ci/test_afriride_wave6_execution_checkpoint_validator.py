"""Tests for the AfriRide Wave 6 execution checkpoint validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_wave6_execution_checkpoint_validator import (
    CONTRACT_DOC,
    AfriRideWave6ExecutionCheckpointValidationError,
    validate_contract,
)


def test_wave6_execution_checkpoint_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.execution_ready_to_run is True
    assert report.pilot_completion_claimed is False
    assert report.production_readiness_claimed is False


def test_execution_checkpoint_locks_operator_sequence() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Run Pilot -> Evidence -> Receipt -> Certification -> GO / NO-GO" in text
    assert "run_pilot" in text
    assert "evidence_bundle" in text
    assert "execution_receipt" in text
    assert "go_no_go_decision" in text


def test_execution_checkpoint_locks_hard_stops() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "replay_mismatch" in text
    assert "identity_drift" in text
    assert "event_missing" in text
    assert "stop_immediately" in text


def test_execution_checkpoint_preserves_no_completion_claim() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "execution_ready_to_run: true" in text
    assert "pilot_completion_claimed: false" in text
    assert "production_readiness_claimed: false" in text
    assert "global_scale_claimed: false" in text
    assert "adversarial_completion_claimed: false" in text


def test_execution_checkpoint_rejects_completion_claim(tmp_path) -> None:
    altered = tmp_path / "checkpoint.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("pilot_completion_claimed: false", "pilot_completion_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideWave6ExecutionCheckpointValidationError,
        match="not verified",
    ):
        validate_contract(altered)
