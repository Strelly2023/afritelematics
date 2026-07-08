from __future__ import annotations

import pytest

from afriride_system.api.main import app


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_guard]


def test_public_pilot_api_contracts_expose_required_surfaces() -> None:
    paths = set(app.openapi()["paths"])
    required = {
        "/auth/token",
        "/v1/public-pilot/registry",
        "/v1/public-pilot/access/check",
        "/v1/public-pilot/limits/check",
        "/v1/public-pilot/reconciliation",
        "/v1/public-pilot/geography",
        "/v1/public-pilot/release/status",
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
        "/ride/{ride_id}/ledger-receipt",
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


def test_public_pilot_api_contracts_preserve_boundaries() -> None:
    spec = app.openapi()
    text = str(spec)
    assert "NovaAI" not in text or "advisory" in text or "advisory only" in text
    assert "/v1/public-pilot/registry" in text
    assert "/v1/public-pilot/limits/check" in text
