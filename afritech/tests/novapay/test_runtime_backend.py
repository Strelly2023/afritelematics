from __future__ import annotations

from pathlib import Path

import pytest

from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.novapay import NovaPayEcosystem


def test_novapay_default_service_allows_sqlite_in_non_production(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "development")
    monkeypatch.setenv("NOVAPAY_PERSISTENCE_BACKEND", "sqlite")
    monkeypatch.setenv("NOVAPAY_DB_PATH", str(tmp_path / "novapay.sqlite3"))

    service = NovaPayEcosystem.default()
    wallet = service.create_wallet(
        owner_id="customer-1",
        organization_id="org-pay",
        owner_type="consumer",
        currency="AUD",
        initial_balance="10.00",
        kyc_status="verified",
    )

    assert wallet["wallet_id"] == "wallet-customer-1-AUD"
    assert service.wallet("wallet-customer-1-AUD")["balance"] == "10.00"


def test_novapay_router_rejects_sqlite_in_production(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "production")
    monkeypatch.setenv("NOVAPAY_PERSISTENCE_BACKEND", "sqlite")
    monkeypatch.setenv("NOVAPAY_DB_PATH", str(tmp_path / "novapay.sqlite3"))

    with pytest.raises(RuntimeError, match="sqlite_not_allowed_in_production"):
        build_novapay_ecosystem_router()
