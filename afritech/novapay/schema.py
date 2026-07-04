"""Canonical NovaPay persistence model names and schema helpers."""

from __future__ import annotations

TABLE_NAMES = (
    "novapay_wallets",
    "novapay_accounts",
    "novapay_ledger_entries",
    "novapay_transactions",
    "novapay_transfers",
    "novapay_qr_codes",
    "novapay_merchants",
    "novapay_agents",
    "novapay_settlements",
    "novapay_reconciliation_batches",
    "novapay_refunds",
    "novapay_disputes",
    "novapay_payouts",
    "novapay_invoices",
    "novapay_receipts",
    "novapay_provider_events",
    "novapay_audit_events",
    "novapay_policy_approvals",
    "novapay_developer_apps",
    "novapay_webhooks",
)


def create_table_sql(table_name: str) -> str:
    return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            record_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
