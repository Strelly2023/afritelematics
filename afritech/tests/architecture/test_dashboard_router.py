from __future__ import annotations

from afritech.core.routing.dashboard_router import (
    DEFAULT_ROUTE,
    dashboard_routes,
    redirect_to_dashboard,
)


def test_dashboard_routes_load_expected_dashboards() -> None:
    routes = dashboard_routes()

    assert routes["afritech"] == "/afritech/dashboard/"
    assert routes["afriride"] == "/afriride/dashboard/"
    assert routes["afroprog"] == "/afroprog/dashboard/"
    assert routes["afriprogramming"] == "/afriprogramming/dashboard/"


def test_redirect_to_dashboard_returns_default_for_unknown_keys() -> None:
    assert redirect_to_dashboard("missing-dashboard") == DEFAULT_ROUTE
