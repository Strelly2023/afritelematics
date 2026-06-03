"""Tests for the AfriRide execution-grade pilot system validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_execution_grade_pilot_system_validator import (
    CONTRACT_DOC,
    AfriRideExecutionGradePilotSystemValidationError,
    validate_contract,
)


def test_execution_grade_pilot_system_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.wave6_framework_complete is True
    assert report.field_evidence_pending is True
    assert report.wave7_authorized is False


def test_execution_grade_pilot_system_preserves_truth_chain() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert (
        "ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> RUNTIME -> TRACE -> REPLAY -> EVIDENCE -> CERTIFICATION"
        in text
    )
    assert "Execute -> Trace -> Replay -> Verify -> Compress -> Certify -> Lock -> Expand" in text
    assert "Launch -> Grow -> Break -> Patch -> Repeat" in text


def test_execution_grade_pilot_system_blocks_synthetic_certification() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "synthetic_may_certify: false" in text
    assert "field_observed_certification_eligible: true" in text


def test_execution_grade_pilot_system_locks_wave7_until_phase_certificates(tmp_path) -> None:
    altered = tmp_path / "execution_grade.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("authorized: false", "authorized: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideExecutionGradePilotSystemValidationError,
        match="wave7 must remain unauthorized",
    ):
        validate_contract(altered)


def test_execution_grade_pilot_system_rejects_guard_drift(tmp_path) -> None:
    altered = tmp_path / "execution_grade.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("synthetic_may_certify: false", "synthetic_may_certify: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRideExecutionGradePilotSystemValidationError,
        match="synthetic evidence must not certify",
    ):
        validate_contract(altered)
