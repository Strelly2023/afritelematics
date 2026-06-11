from __future__ import annotations

import pytest

from afritech.architecture.afritech_dashboard.services import (
    AfriTechDashboardServiceError,
    assert_gateway_payload,
    build_dashboard_gateway_overview,
    build_dashboard_gateway_status,
)


def test_build_dashboard_gateway_overview() -> None:
    payload = build_dashboard_gateway_overview(role="auditor", ride_id="ride-123")

    assert payload["dashboard"]["title"] == "AfriTech Dashboard"
    assert payload["dashboard"]["route"] == "/afritech/dashboard/"
    assert payload["dashboard"]["classification"] == "gateway_read_only"
    assert payload["read_only"] is True
    assert payload["gateway_only"] is True
    assert payload["creates_authority"] is False
    assert len(payload["registry"]) == 4
    assert len(payload["menu"]["links"]) == 3
    assert payload["menu"]["links"][0]["name"] == "AfriRide Dashboard"
    assert payload["role_surface"]["active_role"] == "auditor"
    assert payload["cross_system_context"]["context_id"] == "ride-123"
    assert payload["deep_links"][0]["path"] == "/ride/ride-123/replay"
    assert payload["live_data_wiring"][0]["path"] == "/system/health"


def test_build_dashboard_gateway_status() -> None:
    payload = build_dashboard_gateway_status()

    assert payload["status"] == "ready"
    assert payload["read_only"] is True
    assert payload["projection_only"] is True
    assert payload["creates_authority"] is False


def test_assert_gateway_payload_accepts_valid_payload() -> None:
    assert_gateway_payload(build_dashboard_gateway_status())


def test_assert_gateway_payload_rejects_authority() -> None:
    payload = build_dashboard_gateway_status()
    payload["creates_authority"] = True

    with pytest.raises(AfriTechDashboardServiceError):
        assert_gateway_payload(payload)
