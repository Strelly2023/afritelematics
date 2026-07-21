from __future__ import annotations

from pathlib import Path

import pytest

from afritech.novapay import NovaPayRepository, migrate_legacy_monetary_state


class _TargetRepository:
    def __init__(self) -> None:
        self.writes: list[tuple[str, str, str, str, dict[str, object]]] = []

    def table_names(self) -> tuple[str, ...]:
        return (
            "novapay_wallets",
            "novapay_ledger_entries",
            "novapay_transactions",
        )

    def upsert(
        self,
        table_name: str,
        *,
        record_id: str,
        organization_id: str,
        status: str,
        payload: dict[str, object],
    ) -> object:
        self.writes.append((table_name, record_id, organization_id, status, dict(payload)))
        return payload


def _seed_balanced_source(repo: NovaPayRepository) -> None:
    repo.upsert(
        "novapay_wallets",
        record_id="wallet-1",
        organization_id="org-pay",
        status="active",
        payload={
            "wallet_id": "wallet-1",
            "owner_id": "customer-1",
            "owner_type": "consumer",
            "currency": "AUD",
            "balance": "10.00",
            "metadata": {},
        },
    )
    repo.upsert(
        "novapay_ledger_entries",
        record_id="entry-1",
        organization_id="org-pay",
        status="posted",
        payload={
            "transaction_id": "txn-1",
            "wallet_id": "wallet-1",
            "entry_type": "debit",
            "amount": "10.00",
            "currency": "AUD",
        },
    )
    repo.upsert(
        "novapay_ledger_entries",
        record_id="entry-2",
        organization_id="org-pay",
        status="posted",
        payload={
            "transaction_id": "txn-1",
            "wallet_id": "wallet-2",
            "entry_type": "credit",
            "amount": "10.00",
            "currency": "AUD",
        },
    )


def test_migrate_legacy_monetary_state_reconciles_and_copies_records(tmp_path: Path) -> None:
    source = NovaPayRepository(tmp_path / "source.sqlite3")
    target = _TargetRepository()
    _seed_balanced_source(source)

    report = migrate_legacy_monetary_state(source, target)

    assert report["dry_run"] is False
    assert report["inventory"]["novapay_wallets"] == 1
    assert report["inventory"]["novapay_ledger_entries"] == 2
    assert report["ledger_totals"]["AUD"]["balanced"] is True
    assert len(target.writes) == 3
    assert target.writes[0][0] == "novapay_wallets"


def test_migrate_legacy_monetary_state_rejects_unbalanced_ledger_entries(tmp_path: Path) -> None:
    source = NovaPayRepository(tmp_path / "source.sqlite3")
    target = _TargetRepository()

    source.upsert(
        "novapay_ledger_entries",
        record_id="entry-1",
        organization_id="org-pay",
        status="posted",
        payload={
            "transaction_id": "txn-1",
            "wallet_id": "wallet-1",
            "entry_type": "debit",
            "amount": "10.00",
            "currency": "AUD",
        },
    )
    source.upsert(
        "novapay_ledger_entries",
        record_id="entry-2",
        organization_id="org-pay",
        status="posted",
        payload={
            "transaction_id": "txn-1",
            "wallet_id": "wallet-2",
            "entry_type": "credit",
            "amount": "9.00",
            "currency": "AUD",
        },
    )

    with pytest.raises(ValueError, match="migration_totals_do_not_reconcile"):
        migrate_legacy_monetary_state(source, target)
