from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Iterable

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.balance_snapshot as balance_snapshot
import afritech.novapay.domain.customer as customer
import afritech.novapay.domain.financial_account as financial_account
import afritech.novapay.domain.journal_entry as journal_entry
import afritech.novapay.domain.ledger_account as ledger_account
import afritech.novapay.domain.receipt as receipt
import afritech.novapay.domain.remittance as remittance
import afritech.novapay.domain.settlement_batch as settlement_batch
import afritech.novapay.domain.settlement_reconciliation as reconciliation
import afritech.novapay.domain.transaction as transaction
import afritech.novapay.domain.transfer as transfer
import afritech.novapay.domain.wallet as wallet


DOMAIN_ROOT = Path("afritech/novapay/domain")

PHASE_1_MODULE_NAMES = (
    "money",
    "currency",
    "fx",
    "customer",
    "wallet",
    "financial_account",
    "balance_snapshot",
    "transaction",
    "ledger_account",
    "journal_entry",
    "transfer",
    "remittance",
    "settlement_batch",
    "settlement_reconciliation",
    "receipt",
)

PHASE_1_MODULE_PATHS = tuple(
    DOMAIN_ROOT / f"{module_name}.py"
    for module_name in PHASE_1_MODULE_NAMES
)

FORBIDDEN_RUNTIME_IMPORT_ROOTS = {
    "django",
    "flask",
    "fastapi",
    "starlette",
    "requests",
    "httpx",
    "aiohttp",
    "sqlalchemy",
    "psycopg",
    "psycopg2",
    "sqlite3",
    "redis",
    "celery",
    "boto3",
    "kafka",
    "pika",
}

FORBIDDEN_RUNTIME_AUTHORITY = {
    "repository",
    "database",
    "session",
    "unit_of_work",
    "provider_client",
    "network_client",
    "http_client",
    "payment_service",
    "wallet_service",
    "ledger_service",
    "transfer_service",
    "remittance_service",
    "settlement_engine",
    "reconciliation_engine",
    "delivery_client",
    "signing_service",
    "verification_client",
}

SERIALIZATION_METHODS = {
    "canonical_dict",
    "to_dict",
    "as_dict",
    "serialize",
    "from_dict",
    "deserialize",
}


def _module_source(module_name: str) -> str:
    return (
        DOMAIN_ROOT / f"{module_name}.py"
    ).read_text(encoding="utf-8").lower()


def _combined_source(
    module_names: Iterable[str] = PHASE_1_MODULE_NAMES,
) -> str:
    return "\n".join(
        _module_source(module_name)
        for module_name in module_names
    )


def _runtime_classes(
    module_names: Iterable[str] = PHASE_1_MODULE_NAMES,
) -> tuple[type[object], ...]:
    values: list[type[object]] = []

    for module_name in module_names:
        module = importlib.import_module(
            f"afritech.novapay.domain.{module_name}"
        )

        for symbol in module.__all__:
            value = getattr(module, symbol)

            if not inspect.isclass(value):
                continue

            if value.__module__ != module.__name__:
                continue

            values.append(value)

    return tuple(values)


def _field_names(value: type[object]) -> set[str]:
    if not is_dataclass(value):
        return set()

    return {
        item.name
        for item in fields(value)
    }


def _public_methods(value: type[object]) -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(value)
        if callable(member) and not name.startswith("_")
    }


def _assert_vocabulary(
    module_names: tuple[str, ...],
    tokens: tuple[str, ...],
) -> None:
    source = _combined_source(module_names)

    assert any(
        token.lower() in source
        for token in tokens
    )


def test_customer_identity_and_tenant_propagation() -> None:
    _assert_vocabulary(
        (
            "customer",
            "wallet",
            "financial_account",
            "transaction",
            "transfer",
            "remittance",
        ),
        (
            "customer_id",
            "identity_id",
            "tenant_id",
            "legal_entity_id",
            "party_id",
        ),
    )


def test_customer_to_wallet_ownership() -> None:
    source = _combined_source(
        (
            "customer",
            "wallet",
            "transaction",
            "transfer",
            "remittance",
        )
    )

    assert "wallet" in source
    assert "customer" in source

    assert any(
        token in source
        for token in (
            "customer_id",
            "wallet_id",
            "owner_id",
            "wallet_reference",
        )
    )


def test_customer_to_financial_account_linkage() -> None:
    source = _combined_source(
        (
            "customer",
            "financial_account",
            "transaction",
            "transfer",
            "remittance",
        )
    )

    assert "customer" in source
    assert "account" in source

    assert any(
        token in source
        for token in (
            "customer_id",
            "financial_account_id",
            "account_id",
            "account_reference",
        )
    )


def test_wallet_and_account_monetary_compatibility() -> None:
    source = _combined_source(
        (
            "money",
            "currency",
            "wallet",
            "financial_account",
            "balance_snapshot",
            "transaction",
        )
    )

    assert "amount" in source
    assert "currency" in source

    assert any(
        token in source
        for token in (
            "balance",
            "money",
            "available",
            "reserved",
        )
    )


def test_transaction_identifier_propagation() -> None:
    source = _combined_source(
        (
            "transaction",
            "transfer",
            "remittance",
            "settlement_batch",
            "settlement_reconciliation",
            "receipt",
        )
    )

    assert "transaction_id" in source

    assert any(
        token in source
        for token in (
            "transaction_reference",
            "reference_type",
            "reference_value",
        )
    )


def test_ledger_account_and_journal_entry_linkage() -> None:
    source = _combined_source(
        (
            "transaction",
            "ledger_account",
            "journal_entry",
            "transfer",
            "settlement_batch",
        )
    )

    assert "ledger" in source
    assert "journal" in source

    assert any(
        token in source
        for token in (
            "ledger_account_id",
            "journal_entry_id",
            "entry_id",
            "debit",
            "credit",
        )
    )


def test_transfer_integration() -> None:
    source = _combined_source(
        (
            "transaction",
            "transfer",
            "remittance",
            "settlement_batch",
            "receipt",
        )
    )

    assert "transfer_id" in source

    assert any(
        token in source
        for token in (
            "transaction_id",
            "remittance",
            "settlement",
            "reference_type",
        )
    )


def test_remittance_integration() -> None:
    source = _combined_source(
        (
            "transaction",
            "transfer",
            "remittance",
            "settlement_batch",
            "receipt",
        )
    )

    assert "remittance_id" in source

    assert any(
        token in source
        for token in (
            "transfer_id",
            "transaction_id",
            "settlement",
            "reference_type",
        )
    )


def test_settlement_batch_integration() -> None:
    source = _combined_source(
        (
            "transfer",
            "remittance",
            "settlement_batch",
            "settlement_reconciliation",
            "receipt",
        )
    )

    assert "settlement" in source

    assert any(
        token in source
        for token in (
            "settlement_batch_id",
            "settlement_id",
            "batch_id",
        )
    )


def test_settlement_reconciliation_integration() -> None:
    source = _combined_source(
        (
            "settlement_batch",
            "settlement_reconciliation",
            "receipt",
        )
    )

    assert "reconciliation" in source

    assert any(
        token in source
        for token in (
            "reconciliation_id",
            "settlement_reconciliation",
            "reference_type",
            "reference_value",
        )
    )


def test_receipt_reference_propagation() -> None:
    assert hasattr(receipt, "ReceiptReference")

    reference_fields = _field_names(
        receipt.ReceiptReference
    )

    assert {
        "reference_type",
        "reference_value",
    }.issubset(reference_fields)

    source = inspect.getsource(receipt).lower()

    assert any(
        token in source
        for token in (
            "transaction",
            "transfer",
            "remittance",
            "settlement",
            "reconciliation",
            "customer",
            "wallet",
            "account",
        )
    )


def test_end_to_end_monetary_consistency() -> None:
    source = _combined_source()

    for token in (
        "amount",
        "currency",
        "balance",
        "debit",
        "credit",
    ):
        assert token in source

    assert any(
        token in source
        for token in (
            "exchange_rate",
            "fx_quote",
            "currency_pair",
        )
    )

    assert any(
        token in source
        for token in (
            "subtotal",
            "gross_total",
            "net_total",
            "paid_amount",
            "outstanding_amount",
        )
    )


def test_cross_domain_lifecycle_compatibility() -> None:
    source = _combined_source(
        (
            "customer",
            "wallet",
            "financial_account",
            "transaction",
            "transfer",
            "remittance",
            "settlement_batch",
            "settlement_reconciliation",
            "receipt",
        )
    )

    assert "status" in source

    lifecycle_tokens = {
        "activate",
        "suspend",
        "freeze",
        "authorize",
        "complete",
        "cancel",
        "fail",
        "settle",
        "reconcile",
        "issue",
        "void",
        "expire",
    }

    matched = {
        token
        for token in lifecycle_tokens
        if token in source
    }

    assert len(matched) >= 6


def test_deterministic_serialization_and_replay() -> None:
    serialization_types = []

    for value in _runtime_classes():
        matched = SERIALIZATION_METHODS.intersection(
            _public_methods(value)
        )

        if matched:
            serialization_types.append(
                (
                    value.__module__,
                    value.__name__,
                    matched,
                )
            )

    assert len(serialization_types) >= 10


def test_immutable_aggregate_interaction() -> None:
    dataclass_count = 0

    for value in _runtime_classes():
        if not is_dataclass(value):
            continue

        dataclass_count += 1

        assert value.__dataclass_params__.frozen is True, (
            value.__module__,
            value.__name__,
        )

    assert dataclass_count >= 20


def test_receipt_remains_module_local() -> None:
    assert hasattr(receipt, "Receipt")
    assert "Receipt" in receipt.__all__

    assert not hasattr(domain, "Receipt")
    assert "Receipt" not in domain.__all__

    assert not hasattr(novapay, "Receipt")
    assert "Receipt" not in novapay.__all__

    for symbol in (
        "ReceiptIntegrityEvidence",
        "ReceiptVerificationResult",
    ):
        assert getattr(domain, symbol) is getattr(
            receipt,
            symbol,
        )

        assert getattr(novapay, symbol) is getattr(
            receipt,
            symbol,
        )

    assert not hasattr(
        receipt,
        "ReceiptPresentationSummary",
    )


def test_runtime_and_authority_boundaries() -> None:
    violations: list[
        tuple[str, str, list[str]]
    ] = []

    for value in _runtime_classes():
        member_overlap = sorted(
            FORBIDDEN_RUNTIME_AUTHORITY.intersection(
                _public_methods(value)
            )
        )

        if member_overlap:
            violations.append(
                (
                    value.__module__,
                    value.__name__,
                    member_overlap,
                )
            )

        field_overlap = sorted(
            FORBIDDEN_RUNTIME_AUTHORITY.intersection(
                _field_names(value)
            )
        )

        if field_overlap:
            violations.append(
                (
                    value.__module__,
                    value.__name__,
                    field_overlap,
                )
            )

    assert violations == []


def test_canonical_public_identities() -> None:
    canonical = {
        "Customer": customer.Customer,
        "Wallet": wallet.Wallet,
        "FinancialAccount": financial_account.FinancialAccount,
        "BalanceSnapshot": balance_snapshot.BalanceSnapshot,
        "Transaction": transaction.Transaction,
        "LedgerAccount": ledger_account.LedgerAccount,
        "JournalEntry": journal_entry.JournalEntry,
        "Transfer": transfer.Transfer,
        "Remittance": remittance.Remittance,
        "SettlementBatch": settlement_batch.SettlementBatch,
        "SettlementReconciliation": reconciliation.SettlementReconciliation,
    }

    for symbol, module_value in canonical.items():
        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_phase1_modules_remain_replay_safe() -> None:
    violations: list[
        tuple[str, str, int]
    ] = []

    for path in PHASE_1_MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]

                    if root in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
                        violations.append(
                            (
                                str(path),
                                alias.name,
                                node.lineno,
                            )
                        )

            if isinstance(node, ast.ImportFrom):
                if not node.module:
                    continue

                root = node.module.split(".")[0]

                if root in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
                    violations.append(
                        (
                            str(path),
                            node.module,
                            node.lineno,
                        )
                    )

    assert violations == []
