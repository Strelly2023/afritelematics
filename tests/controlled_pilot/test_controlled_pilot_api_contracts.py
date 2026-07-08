from __future__ import annotations

import pytest

from afriride_system.api.main import app


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_api]


def test_controlled_pilot_api_contracts_expose_required_surfaces() -> None:
    paths = set(app.openapi()["paths"])
    required = {
        "/auth/token",
        "/passenger/request-ride",
        "/driver/status",
        "/driver/requests/{driver_id}",
        "/driver/accept",
        "/driver/start",
        "/driver/arrive",
        "/driver/complete",
        "/ride/{ride_id}/receipt",
        "/ride/{ride_id}/replay",
        "/ride/{ride_id}/evidence",
        "/v1/pilot/registry",
        "/v1/pilot/access/check",
        "/v1/pilot/devices/bind",
        "/v1/pilot/devices/revoke",
        "/v1/pilot/support/tickets",
        "/v1/pilot/safety/sos",
        "/v1/payments/charges",
        "/v1/payments/transactions/{transaction_id}/refunds",
        "/v1/payments/wallets/{owner_type}/{owner_id}/{currency}",
        "/v1/payments/transactions/{transaction_id}/disputes",
        "/v1/payments/payouts",
        "/v1/payments/reporting",
        "/v1/payments/health",
        "/v1/operations/dashboard",
        "/v1/operations/launch-readiness",
        "/v1/operations/safety/incidents",
        "/v1/corridors",
        "/v1/treasury/snapshot",
        "/health",
    }
    assert required.issubset(paths)


def test_controlled_pilot_api_contracts_preserve_boundaries() -> None:
    spec = app.openapi()
    text = str(spec)
    assert "NovaAI" not in text or "advisory" in text or "advisory only" in text
    assert "/v1/pilot/registry" in text
    assert "/v1/payments/charges" in text
