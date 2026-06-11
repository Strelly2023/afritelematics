from __future__ import annotations

import pytest

from afritech.architecture.afritech_dashboard.views import (
    AfriTechDashboardViewError,
    ensure_gateway_view_boundary,
    render_dashboard_gateway_overview_view,
    render_dashboard_gateway_status_view,
)


def test_render_dashboard_gateway_overview_view() -> None:
    view = render_dashboard_gateway_overview_view()

    assert view["view"] == "afritech_dashboard_gateway_overview"
    assert view["payload"]["dashboard"]["title"] == "AfriTech Dashboard"
    assert view["read_only"] is True
    assert view["gateway_only"] is True
    assert view["creates_authority"] is False


def test_render_dashboard_gateway_status_view() -> None:
    view = render_dashboard_gateway_status_view()

    assert view["view"] == "afritech_dashboard_gateway_status"
    assert view["payload"]["status"] == "ready"
    assert view["projection_only"] is True


def test_ensure_gateway_view_boundary_accepts_valid_view() -> None:
    ensure_gateway_view_boundary(render_dashboard_gateway_status_view())


def test_ensure_gateway_view_boundary_rejects_mutation() -> None:
    payload = render_dashboard_gateway_status_view()
    payload["mutates_view"] = True

    with pytest.raises(AfriTechDashboardViewError):
        ensure_gateway_view_boundary(payload)
