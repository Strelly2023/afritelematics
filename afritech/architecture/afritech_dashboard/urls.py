"""Declared URL surfaces for the AfriTech dashboard gateway."""

from __future__ import annotations


urlpatterns = (
    {
        "path": "/afritech/dashboard/",
        "view": "afritech_dashboard_gateway_overview",
        "name": "afritech-dashboard",
    },
    {
        "path": "/afritech/dashboard/status/",
        "view": "afritech_dashboard_gateway_status",
        "name": "afritech-dashboard-status",
    },
)


__all__ = ["urlpatterns"]
