from __future__ import annotations

from pathlib import Path

import pytest

from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.novapay import NovaPayEcosystem
from afritech.novapay.repository import build_repository_from_environment


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


def test_novapay_repository_prefers_postgres_when_database_url_is_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "development")
    monkeypatch.setenv("NOVAPAY_DATABASE_URL", "postgresql://example/db")
    monkeypatch.delenv("NOVAPAY_PERSISTENCE_BACKEND", raising=False)

    class _DummyRepo:
        def __init__(self, dsn: str) -> None:
            self.dsn = dsn

        def close(self) -> None:  # pragma: no cover - compatibility hook
            return None

    monkeypatch.setattr("afritech.novapay.repository.PostgresNovaPayRepository", _DummyRepo)
    repo = build_repository_from_environment()
    assert isinstance(repo, _DummyRepo)
    assert repo.dsn == "postgresql://example/db"


def test_novapay_repository_fails_closed_in_production_without_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AFRITECH_ENV", "production")
    monkeypatch.delenv("NOVAPAY_PERSISTENCE_BACKEND", raising=False)
    monkeypatch.delenv("NOVAPAY_DATABASE_URL", raising=False)
    monkeypatch.delenv("NOVAPAY_POSTGRES_DSN", raising=False)

    with pytest.raises(RuntimeError, match="sqlite_not_allowed_in_production"):
        build_repository_from_environment()
