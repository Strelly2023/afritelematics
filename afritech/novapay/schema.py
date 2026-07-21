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


POSTGRES_TABLE_EXTRAS: dict[str, tuple[str, ...]] = {
    "novapay_wallets": (
        "wallet_id TEXT NOT NULL",
        "owner_id TEXT NOT NULL",
        "owner_type TEXT NOT NULL",
        "currency TEXT NOT NULL",
        "balance NUMERIC(20,2) NOT NULL DEFAULT 0",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_accounts": (
        "wallet_id TEXT",
        "account_type TEXT",
        "currency TEXT",
        "owner_id TEXT",
        "balance NUMERIC(20,2) NOT NULL DEFAULT 0",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_ledger_entries": (
        "transaction_id TEXT NOT NULL",
        "wallet_id TEXT NOT NULL",
        "entry_type TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "posted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ),
    "novapay_transactions": (
        "transaction_id TEXT NOT NULL",
        "transfer_id TEXT NOT NULL",
        "actor_id TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "sender_wallet_id TEXT NOT NULL",
        "receiver_wallet_id TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "transfer_type TEXT NOT NULL",
        "provider TEXT NOT NULL",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
        "idempotency_key TEXT",
    ),
    "novapay_transfers": (
        "transaction_id TEXT NOT NULL",
        "transfer_id TEXT NOT NULL",
        "actor_id TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "sender_wallet_id TEXT NOT NULL",
        "receiver_wallet_id TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "transfer_type TEXT NOT NULL",
        "provider TEXT NOT NULL",
        "sender_after_json JSONB NOT NULL DEFAULT '{}'::jsonb",
        "receiver_after_json JSONB NOT NULL DEFAULT '{}'::jsonb",
        "idempotency_key TEXT",
    ),
    "novapay_qr_codes": (
        "qr_code TEXT NOT NULL",
        "merchant_wallet_id TEXT NOT NULL",
        "currency TEXT NOT NULL",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_merchants": (
        "merchant_id TEXT NOT NULL",
        "wallet_id TEXT",
        "currency TEXT",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_agents": (
        "movement_id TEXT NOT NULL",
        "wallet_id TEXT NOT NULL",
        "direction TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "wallet_after_json JSONB NOT NULL DEFAULT '{}'::jsonb",
        "idempotency_key TEXT",
    ),
    "novapay_settlements": (
        "settlement_id TEXT NOT NULL",
        "transaction_id TEXT NOT NULL",
        "provider_reference TEXT",
        "settlement_amount NUMERIC(20,2)",
        "currency TEXT",
    ),
    "novapay_reconciliation_batches": (
        "batch_id TEXT NOT NULL",
        "batch_name TEXT NOT NULL",
        "transaction_count INTEGER NOT NULL DEFAULT 0",
        "gross_amount NUMERIC(20,2) NOT NULL DEFAULT 0",
    ),
    "novapay_refunds": (
        "refund_id TEXT NOT NULL",
        "transaction_id TEXT NOT NULL",
        "reason TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "approval_status TEXT NOT NULL",
    ),
    "novapay_disputes": (
        "dispute_id TEXT NOT NULL",
        "transaction_id TEXT NOT NULL",
        "reason TEXT NOT NULL",
        "opened_by TEXT NOT NULL",
        "opened_role TEXT NOT NULL",
        "idempotency_key TEXT",
    ),
    "novapay_payouts": (
        "payout_id TEXT NOT NULL",
        "source_wallet_id TEXT NOT NULL",
        "destination_reference TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "scheduled_for TEXT",
        "actor_id TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "idempotency_key TEXT",
    ),
    "novapay_invoices": (
        "invoice_id TEXT NOT NULL",
        "customer_wallet_id TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "currency TEXT NOT NULL",
        "reference TEXT NOT NULL",
        "due_date TEXT",
        "actor_id TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "idempotency_key TEXT",
    ),
    "novapay_receipts": (
        "receipt_id TEXT NOT NULL",
        "transaction_id TEXT NOT NULL",
        "actor_id TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "trust_hash TEXT NOT NULL",
        "signature_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_provider_events": (
        "provider TEXT NOT NULL",
        "event_type TEXT NOT NULL",
        "transaction_id TEXT NOT NULL",
        "receipt_id TEXT",
    ),
    "novapay_audit_events": (
        "actor_id TEXT NOT NULL",
        "role TEXT NOT NULL",
        "action TEXT NOT NULL",
        "transaction_id TEXT",
        "receipt_id TEXT",
    ),
    "novapay_policy_approvals": (
        "decision_id TEXT NOT NULL",
        "request_id TEXT NOT NULL",
        "subject_id TEXT NOT NULL",
        "role TEXT NOT NULL",
        "action TEXT NOT NULL",
        "amount NUMERIC(20,2) NOT NULL",
        "limit_amount NUMERIC(20,2) NOT NULL",
        "approved BOOLEAN NOT NULL DEFAULT FALSE",
        "requires_manual_review BOOLEAN NOT NULL DEFAULT FALSE",
        "workflow TEXT NOT NULL",
        "reason TEXT NOT NULL",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_developer_apps": (
        "app_id TEXT NOT NULL",
        "developer_id TEXT NOT NULL",
        "app_name TEXT NOT NULL",
        "api_key_hash TEXT NOT NULL",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
    "novapay_webhooks": (
        "webhook_id TEXT NOT NULL",
        "app_id TEXT",
        "developer_id TEXT NOT NULL",
        "webhook_url TEXT NOT NULL",
        "event_types_json JSONB NOT NULL DEFAULT '[]'::jsonb",
        "secret_hint TEXT",
        "delivery_status TEXT NOT NULL DEFAULT 'pending'",
        "metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    ),
}


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


def create_postgres_table_sql(table_name: str) -> str:
    extras = POSTGRES_TABLE_EXTRAS.get(table_name, ())
    extra_sql = ",\n            ".join(extras)
    if extra_sql:
        extra_sql = ",\n            " + extra_sql
    return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            record_id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            status TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            idempotency_key TEXT UNIQUE,
            payload_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(){extra_sql}
        )
    """
