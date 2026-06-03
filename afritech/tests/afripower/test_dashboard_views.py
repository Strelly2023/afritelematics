from __future__ import annotations

import pytest

from afritech.afripower.dashboard.views import (
    AFRIPowerDashboardViewError,
    ensure_dashboard_view_boundary,
    render_dashboard_overview_view,
    render_dashboard_status_view,
    render_dashboard_summary_view,
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


def test_render_dashboard_overview_view():
    view = render_dashboard_overview_view(
        _references(),
        insight_count=2,
    )

    assert view["view"] == "afripower_dashboard_overview"
    assert "payload" in view

    assert view["read_only"] is True
    assert view["reference_only"] is True
    assert view["display_only"] is True
    assert view["projection_only"] is True
    assert view["enterprise_intelligence_only"] is True

    assert view["creates_authority"] is False
    assert view["validates_truth"] is False
    assert view["executes_runtime"] is False
    assert view["mutates_view"] is False
    assert view["mutates_dashboard"] is False
    assert view["mutates_artifacts"] is False


def test_render_dashboard_summary_view():
    view = render_dashboard_summary_view(
        _references(),
        insight_count=2,
    )

    assert view["view"] == "afripower_dashboard_summary"
    assert "payload" in view

    assert view["read_only"] is True
    assert view["creates_authority"] is False
    assert view["validates_truth"] is False
    assert view["executes_runtime"] is False
    assert view["mutates_view"] is False


def test_render_dashboard_status_view():
    view = render_dashboard_status_view()

    assert view["view"] == "afripower_dashboard_status"
    assert view["payload"]["status"] == "ready"

    assert view["read_only"] is True
    assert view["reference_only"] is True
    assert view["display_only"] is True
    assert view["projection_only"] is True
    assert view["enterprise_intelligence_only"] is True

    assert view["creates_authority"] is False
    assert view["validates_truth"] is False
    assert view["executes_runtime"] is False


def test_ensure_dashboard_view_boundary_accepts_valid_view():
    view = render_dashboard_status_view()

    ensure_dashboard_view_boundary(view)


@pytest.mark.parametrize(
    "field",
    (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "enterprise_intelligence_only",
    ),
)
def test_ensure_dashboard_view_boundary_rejects_required_true_field(
    field: str,
):
    view = render_dashboard_status_view()
    view[field] = False

    with pytest.raises(AFRIPowerDashboardViewError):
        ensure_dashboard_view_boundary(view)


@pytest.mark.parametrize(
    "field",
    (
        "creates_authority",
        "validates_truth",
        "executes_runtime",
        "mutates_view",
        "mutates_dashboard",
        "mutates_artifacts",
        "influences_runtime",
        "influences_replay",
        "influences_proof",
        "influences_ci",
        "influences_governance",
    ),
)
def test_ensure_dashboard_view_boundary_rejects_required_false_field(
    field: str,
):
    view = render_dashboard_status_view()
    view[field] = True

    with pytest.raises(AFRIPowerDashboardViewError):
        ensure_dashboard_view_boundary(view)


def test_dashboard_overview_view_is_deterministic():
    first = render_dashboard_overview_view(
        _references(),
        insight_count=2,
    )
    second = render_dashboard_overview_view(
        _references(),
        insight_count=2,
    )

    assert first == second


def test_dashboard_summary_view_is_deterministic():
    first = render_dashboard_summary_view(
        _references(),
        insight_count=2,
    )
    second = render_dashboard_summary_view(
        _references(),
        insight_count=2,
    )

    assert first == second


def test_dashboard_status_view_is_deterministic():
    assert render_dashboard_status_view() == render_dashboard_status_view()
