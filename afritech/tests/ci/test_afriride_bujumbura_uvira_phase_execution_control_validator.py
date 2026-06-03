"""Tests for the AfriRide Bujumbura/Uvira phase execution control validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_bujumbura_uvira_phase_execution_control_validator import (
    CONTRACT_DOC,
    AfriRideBujumburaUviraPhaseExecutionControlValidationError,
    validate_contract,
)


def test_bujumbura_uvira_phase_execution_control_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.location == "Bujumbura_Uvira"
    assert report.phase_ready_to_run is True
    assert report.phase_passed_claimed is False


def test_bujumbura_uvira_phase_locks_c1_to_d2_order() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "C1 -> C2 -> C3 -> D1 -> D2" in text
    assert "C1: cross_border_identity_continuity" in text
    assert "D2: conflicting_claims_preserved_neutrally" in text


def test_bujumbura_uvira_phase_locks_infrastructure_hard_stops() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "event_loss" in text
    assert "state_depends_on_network_timing" in text
    assert "silent_gps_correction" in text
    assert "silent_dispute_resolution" in text


def test_bujumbura_uvira_phase_preserves_resilience_law() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "Network conditions MAY vary" in text
    assert "Execution outcome MUST NOT vary" in text
    assert "operator_law: system_immunity_to_infrastructure_failure" in text
    assert "phase_passed_claimed: false" in text


def test_bujumbura_uvira_phase_rejects_pass_claim(tmp_path) -> None:
    altered = tmp_path / "bujumbura_uvira.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("phase_passed_claimed: false", "phase_passed_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideBujumburaUviraPhaseExecutionControlValidationError,
        match="not verified",
    ):
        validate_contract(altered)
