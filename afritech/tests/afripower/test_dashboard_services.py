from __future__ import annotations

import pytest

from afritech.afripower.dashboard.services import (
    AFRIPowerDashboardServiceError,
    assert_dashboard_service_payload,
    build_dashboard_overview,
    build_dashboard_status,
    build_dashboard_summary,
)


def _references():
    return (
        {
            "execution_id": "exec.001",
            "traceability": [
                {"type": "Proof", "id": "proof.001"},
                {"type": "ADR", "id": "ADR-001"},
            ],
        },
        {
            "receipt_id": "receipt.001",
            "receipt_type": "proof_reference",
        },
    )


def test_build_dashboard_overview():
    payload = build_dashboard_overview(
        _references(),
        insight_count=2,
    )

    assert payload["read_only"] is True
    assert payload["reference_only"] is True
    assert payload["display_only"] is True
    assert payload["projection_only"] is True
    assert payload["enterprise_intelligence_only"] is True

    assert payload["creates_authority"] is False
    assert payload["validates_truth"] is False
    assert payload["executes_runtime"] is False
    assert payload["mutates_dashboard"] is False
    assert payload["mutates_artifacts"] is False

    assert payload["reference_count"] == 2
    assert "dashboard" in payload
    assert "graph" in payload
    assert "graph_summary" in payload
    assert "metrics" in payload


def test_build_dashboard_summary():
    payload = build_dashboard_summary(
        _references(),
        insight_count=2,
    )

    assert payload["read_only"] is True
    assert payload["creates_authority"] is False
    assert payload["validates_truth"] is False
    assert payload["executes_runtime"] is False

    assert payload["reference_count"] == 2
    assert "dashboard" in payload
    assert "graph_summary" in payload
    assert "metrics" in payload
    assert "graph" not in payload


def test_build_dashboard_status():
    payload = build_dashboard_status()

    assert payload["status"] == "ready"
    assert payload["read_only"] is True
    assert payload["reference_only"] is True
    assert payload["display_only"] is True
    assert payload["projection_only"] is True
    assert payload["enterprise_intelligence_only"] is True
    assert payload["creates_authority"] is False
    assert payload["validates_truth"] is False
    assert payload["executes_runtime"] is False


def test_assert_dashboard_service_payload_accepts_valid_payload():
    payload = build_dashboard_status()

    assert_dashboard_service_payload(payload)


def test_assert_dashboard_service_payload_rejects_authority():
    payload = build_dashboard_status()
    payload["creates_authority"] = True

    with pytest.raises(AFRIPowerDashboardServiceError):
        assert_dashboard_service_payload(payload)


def test_assert_dashboard_service_payload_rejects_truth_validation():
    payload = build_dashboard_status()
    payload["validates_truth"] = True

    with pytest.raises(AFRIPowerDashboardServiceError):
        assert_dashboard_service_payload(payload)


def test_assert_dashboard_service_payload_rejects_runtime_execution():
    payload = build_dashboard_status()
    payload["executes_runtime"] = True

    with pytest.raises(AFRIPowerDashboardServiceError):
        assert_dashboard_service_payload(payload)


def test_dashboard_overview_is_deterministic():
    first = build_dashboard_overview(
        _references(),
        insight_count=2,
    )
    second = build_dashboard_overview(
        _references(),
        insight_count=2,
    )

    assert first == second


def test_dashboard_summary_is_deterministic():
    first = build_dashboard_summary(
        _references(),
        insight_count=2,
    )
    second = build_dashboard_summary(
        _references(),
        insight_count=2,
    )

    assert first == second


def test_dashboard_status_is_deterministic():
    assert build_dashboard_status() == build_dashboard_status()
