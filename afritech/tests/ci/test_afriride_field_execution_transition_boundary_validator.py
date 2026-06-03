"""Tests for the AfriRide field execution transition boundary validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_field_execution_transition_boundary_validator import (
    CONTRACT_DOC,
    AfriRideFieldExecutionTransitionBoundaryValidationError,
    validate_contract,
)


def test_field_execution_transition_boundary_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.governance_machine_exists is True
    assert report.operational_evidence_present is False
    assert report.field_execution_performed is False
    assert report.wave7_authorized is False


def test_field_execution_transition_boundary_preserves_claim_discipline() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "The AfriRide governance machine exists. That is an architectural claim." in text
    assert "These are architectural claims only." in text
    assert "Operational Evidence: NOT_PRESENT" in text
    assert "Operational Certification: NOT_ADMISSIBLE" in text
    assert "Reality is the only authority that can advance the system." in text
    assert "Governance can define truth. Only reality can prove it." in text
    assert "The system is now incapable of advancing itself." in text
    assert (
        "Only reality interacting with the system under governance constraints can produce the next state."
        in text
    )
    assert "No other entry point exists." in text
    assert "Repository Scope: TERMINAL_PRE_OPERATIONAL" in text
    assert "Authority Source: EXTERNAL_REALITY" in text


def test_field_execution_transition_boundary_blocks_synthetic_authority() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "may_not_certify" in text
    assert "may_not_authorize_wave7" in text
    assert "may_certify: false" in text
    assert "may_authorize_wave7: false" in text


def test_field_execution_transition_boundary_rejects_wave7_unlock_by_ci(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("certified_operational_evidence", "ci_success"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="Wave 7 unlock requirements mismatch",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_operational_claim_inflation(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("operational_evidence_present: false", "operational_evidence_present: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="not verified",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_non_reality_advancement(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("advancement_authority: reality_only", "advancement_authority: ci_success"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="advancement authority must be reality_only",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_reality_interface_activation(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace(
            "reality_interface:\n      state: NOT_YET_ACTIVATED",
            "reality_interface:\n      state: ACTIVATED",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="reality interface must remain not yet activated",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_repository_legitimacy_claim(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace(
            "repository_outputs_can_produce_operational_legitimacy: false",
            "repository_outputs_can_produce_operational_legitimacy: true",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="repository outputs must not produce operational legitimacy",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_self_advancement(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("system_can_advance_itself: false", "system_can_advance_itself: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="system must be incapable of advancing itself",
    ):
        validate_contract(altered)


def test_field_execution_transition_boundary_rejects_validator_unlock_path(tmp_path) -> None:
    altered = tmp_path / "field_boundary.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("    - validators\n", ""),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideFieldExecutionTransitionBoundaryValidationError,
        match="Wave 7 forbidden unlocks mismatch",
    ):
        validate_contract(altered)
