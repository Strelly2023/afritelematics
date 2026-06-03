from __future__ import annotations

import pytest

from afritech.afripower.dashboard import constants as dashboard_constants


def test_dashboard_identity():
    assert dashboard_constants.DASHBOARD_COMPONENT == "AFRIPowerDashboard"
    assert dashboard_constants.DASHBOARD_COMPONENT_ID == (
        "afritech.afripower.dashboard"
    )
    assert dashboard_constants.DASHBOARD_VERSION == "1.0"


def test_dashboard_status_and_mode():
    assert dashboard_constants.DASHBOARD_STATUS == "OBSERVATIONAL_ONLY"
    assert dashboard_constants.DASHBOARD_MODE == (
        "READ_ONLY_ENTERPRISE_INTELLIGENCE_DASHBOARD"
    )
    assert dashboard_constants.DASHBOARD_PROJECTION_STATUS == (
        "ENTERPRISE_INTELLIGENCE_PROJECTION"
    )


def test_dashboard_safe_flags_are_true():
    assert dashboard_constants.DASHBOARD_READ_ONLY is True
    assert dashboard_constants.DASHBOARD_REFERENCE_ONLY is True
    assert dashboard_constants.DASHBOARD_DISPLAY_ONLY is True
    assert dashboard_constants.DASHBOARD_PROJECTION_ONLY is True
    assert dashboard_constants.DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY is True


def test_dashboard_authority_flags_are_false():
    assert dashboard_constants.DASHBOARD_AUTHORITATIVE is False
    assert dashboard_constants.DASHBOARD_CREATES_AUTHORITY is False
    assert dashboard_constants.DASHBOARD_VALIDATES_TRUTH is False
    assert dashboard_constants.DASHBOARD_EXECUTES_RUNTIME is False
    assert dashboard_constants.DASHBOARD_MUTATES_ARTIFACTS is False
    assert dashboard_constants.DASHBOARD_MUTATES_RECEIPTS is False
    assert dashboard_constants.DASHBOARD_MUTATES_PROOFS is False
    assert dashboard_constants.DASHBOARD_INFLUENCES_RUNTIME is False
    assert dashboard_constants.DASHBOARD_INFLUENCES_REPLAY is False
    assert dashboard_constants.DASHBOARD_INFLUENCES_PROOF is False
    assert dashboard_constants.DASHBOARD_INFLUENCES_CI is False
    assert dashboard_constants.DASHBOARD_INFLUENCES_GOVERNANCE is False


def test_dashboard_widget_types():
    assert "summary" in dashboard_constants.DASHBOARD_WIDGET_TYPES
    assert "metric" in dashboard_constants.DASHBOARD_WIDGET_TYPES
    assert "graph" in dashboard_constants.DASHBOARD_WIDGET_TYPES
    assert "insight" in dashboard_constants.DASHBOARD_WIDGET_TYPES


def test_dashboard_metric_types():
    assert "node_count" in dashboard_constants.DASHBOARD_METRIC_TYPES
    assert "edge_count" in dashboard_constants.DASHBOARD_METRIC_TYPES
    assert "receipt_count" in dashboard_constants.DASHBOARD_METRIC_TYPES
    assert "insight_count" in dashboard_constants.DASHBOARD_METRIC_TYPES


def test_dashboard_output_formats():
    assert dashboard_constants.DASHBOARD_ALLOWED_OUTPUT_FORMATS == (
        "dict",
        "json",
        "table",
    )


def test_dashboard_metadata_preserves_boundary():
    metadata = dashboard_constants.dashboard_metadata()

    assert metadata["component"] == "AFRIPowerDashboard"
    assert metadata["read_only"] is True
    assert metadata["reference_only"] is True
    assert metadata["display_only"] is True
    assert metadata["projection_only"] is True
    assert metadata["enterprise_intelligence_only"] is True
    assert metadata["authoritative"] is False
    assert metadata["creates_authority"] is False
    assert metadata["validates_truth"] is False
    assert metadata["executes_runtime"] is False
    assert metadata["mutates_artifacts"] is False
    assert metadata["mutates_receipts"] is False
    assert metadata["mutates_proofs"] is False


def test_dashboard_metadata_is_deterministic():
    assert (
        dashboard_constants.dashboard_metadata()
        == dashboard_constants.dashboard_metadata()
    )


def test_assert_dashboard_constants_passes():
    dashboard_constants.assert_dashboard_constants()


def test_assert_dashboard_constants_fails_on_authority(monkeypatch):
    monkeypatch.setattr(
        dashboard_constants,
        "DASHBOARD_AUTHORITATIVE",
        True,
    )

    with pytest.raises(RuntimeError):
        dashboard_constants.assert_dashboard_constants()


def test_assert_dashboard_constants_fails_on_truth_validation(monkeypatch):
    monkeypatch.setattr(
        dashboard_constants,
        "DASHBOARD_VALIDATES_TRUTH",
        True,
    )

    with pytest.raises(RuntimeError):
        dashboard_constants.assert_dashboard_constants()


def test_assert_dashboard_constants_fails_on_runtime_execution(monkeypatch):
    monkeypatch.setattr(
        dashboard_constants,
        "DASHBOARD_EXECUTES_RUNTIME",
        True,
    )

    with pytest.raises(RuntimeError):
        dashboard_constants.assert_dashboard_constants()


def test_assert_dashboard_constants_fails_on_receipt_mutation(monkeypatch):
    monkeypatch.setattr(
        dashboard_constants,
        "DASHBOARD_MUTATES_RECEIPTS",
        True,
    )

    with pytest.raises(RuntimeError):
        dashboard_constants.assert_dashboard_constants()


def test_assert_dashboard_constants_fails_on_missing_read_only(monkeypatch):
    monkeypatch.setattr(
        dashboard_constants,
        "DASHBOARD_READ_ONLY",
        False,
    )

    with pytest.raises(RuntimeError):
        dashboard_constants.assert_dashboard_constants()
