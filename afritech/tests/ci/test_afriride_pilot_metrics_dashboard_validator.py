"""Tests for the AfriRide pilot metrics dashboard validator."""

from __future__ import annotations

import pytest

from afritech.ci.afriride_pilot_metrics_dashboard_validator import (
    AfriRidePilotMetricsDashboardValidationError,
    CONTRACT_DOC,
    validate_contract,
)


def test_pilot_metrics_dashboard_contract_is_verified() -> None:
    report = validate_contract()

    assert report.verified is True
    assert report.live_defines_truth is False
    assert report.ci_defines_admissibility is True
    assert report.replay_defines_truth is True
    assert report.pilot_completion_claimed is False


def test_dashboard_contract_preserves_live_ci_separation() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "LIVE reflects behavior" in text
    assert "CI defines admissibility" in text
    assert "Live dashboard may show success" in text
    assert "CI dashboard decides if it is real success" in text


def test_dashboard_contract_locks_tier1_metrics() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "replay_success_rate: \"100%\"" in text
    assert "identity_drift: 0" in text
    assert "execution_divergence: 0" in text
    assert "event_corruption: 0" in text


def test_dashboard_contract_locks_hard_stop_alerts() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    assert "replay_mismatch" in text
    assert "identity_drift" in text
    assert "determinism_violation" in text
    assert "critical_alert_action: hard_stop_pilot" in text


def test_dashboard_validator_rejects_completion_claim(tmp_path) -> None:
    altered = tmp_path / "dashboard.md"
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    altered.write_text(
        text.replace("pilot_completion_claimed: false", "pilot_completion_claimed: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        AfriRidePilotMetricsDashboardValidationError,
        match="not verified",
    ):
        validate_contract(altered)
