from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from afriride_system.api.main import app


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_api, pytest.mark.contract]


REQUIRED_PATHS = [
    "/auth/register",
    "/auth/login",
    "/auth/logout",
    "/auth/otp/send",
    "/auth/otp/verify",
    "/novaid/profile",
    "/novaid/verify/personal",
    "/novaid/verify/business",
    "/novaid/verify/employee",
    "/novaid/verify/partner",
    "/novaid/verify/inspector",
    "/novaid/documents/upload",
    "/novaid/activity",
    "/novaid/audit",
    "/novapay/wallet",
    "/novapay/balance",
    "/novapay/topup",
    "/novapay/send",
    "/novapay/receive",
    "/novapay/cash-in",
    "/novapay/cash-out",
    "/novapay/qr/generate",
    "/novapay/merchant/pay",
    "/novapay/refunds",
    "/novapay/settlements",
    "/novapay/business/approvals",
    "/novapay/business/payroll",
    "/rides/request",
    "/rides/accept",
    "/rides/start",
    "/rides/end",
    "/rides/cancel",
    "/rides/history",
    "/drivers/status",
    "/operators/fleet",
    "/operators/compliance",
    "/support/tickets",
    "/safety/sos",
    "/security/devices",
]


def test_internal_qa_api_contracts_are_present_or_mocked() -> None:
    paths = app.openapi()["paths"]
    for path in REQUIRED_PATHS:
        assert path in paths or f"/v1{path}" in paths, f"missing API contract surface: {path}"


def test_internal_qa_versioned_auth_and_protected_routes_work() -> None:
    client = TestClient(app)
    token = client.post("/v1/auth/token", json={"user_id": "qa-operator", "role": "ADMIN"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/v1/architecture/signature", headers=headers).status_code == 200
    assert client.get("/v1/corridors", headers=headers).status_code == 200
    assert client.get("/v1/treasury/snapshot", headers=headers).status_code == 200
    assert client.get("/v1/architecture/signature").status_code == 401
    assert client.get("/v1/treasury/snapshot").status_code == 401
