"""Read-only AfriTech dashboard gateway surfaces."""

from afritech.architecture.afritech_dashboard.services import (
    AfriTechDashboardServiceError,
    assert_gateway_payload,
    build_dashboard_gateway_overview,
    build_dashboard_gateway_status,
)
from afritech.architecture.afritech_dashboard.views import (
    AfriTechDashboardViewError,
    ensure_gateway_view_boundary,
    render_dashboard_gateway_overview_view,
    render_dashboard_gateway_status_view,
)

__all__ = [
    "AfriTechDashboardServiceError",
    "AfriTechDashboardViewError",
    "assert_gateway_payload",
    "build_dashboard_gateway_overview",
    "build_dashboard_gateway_status",
    "ensure_gateway_view_boundary",
    "render_dashboard_gateway_overview_view",
    "render_dashboard_gateway_status_view",
]
