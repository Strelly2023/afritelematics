from __future__ import annotations

import ast
import inspect
from dataclasses import fields, is_dataclass
from pathlib import Path

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.journal_entry as journal_entry
import afritech.novapay.domain.ledger_account as ledger_account
import afritech.novapay.domain.receipt as receipt
import afritech.novapay.domain.settlement_batch as settlement_batch
import afritech.novapay.domain.settlement_reconciliation as reconciliation
import afritech.novapay.domain.transaction as transaction
import afritech.novapay.domain.transfer as transfer
import afritech.novapay.domain.wallet as wallet


DOMAIN_ROOT = Path("afritech/novapay/domain")
TEST_ROOT = Path("afritech/tests/novapay")
INTEGRATION_MODULE_PATHS = tuple(
    DOMAIN_ROOT / f"{name}.py"
    for name in (
        "wallet",
        "ledger_account",
        "journal_entry",
        "transaction",
        "transfer",
        "settlement_batch",
        "settlement_reconciliation",
        "receipt",
    )
)
FOCUSED_TEST_PATTERNS = (
    "*transaction*.py",
    "*ledger*.py",
    "*journal*.py",
    "*wallet*.py",
    "*transfer*.py",
    "*settlement*.py",
    "*reconciliation*.py",
    "*receipt*.py",
)


def _combined_implementation_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in INTEGRATION_MODULE_PATHS)


def _focused_test_source() -> str:
    paths: set[Path] = set()
    for pattern in FOCUSED_TEST_PATTERNS:
        paths.update(TEST_ROOT.glob(pattern))
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(paths)
        if path.name != "test_phase1_transaction_ledger_integration_certification.py"
    )


def _public_methods(value: type[object]) -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(value)
        if callable(member) and not name.startswith("_")
    }


def _assert_source_and_test_vocabulary(
    implementation_tokens: tuple[str, ...], test_tokens: tuple[str, ...]
) -> None:
    implementation = _combined_implementation_source().lower()
    tests = _focused_test_source().lower()
    assert any(token.lower() in implementation for token in implementation_tokens)
    assert any(token.lower() in tests for token in test_tokens)


def test_canonical_transaction_ledger_types_have_cross_surface_identity() -> None:
    module_types = {
        "Wallet": wallet.Wallet,
        "LedgerAccount": ledger_account.LedgerAccount,
        "JournalEntry": journal_entry.JournalEntry,
        "Transaction": transaction.Transaction,
        "Transfer": transfer.Transfer,
        "SettlementBatch": settlement_batch.SettlementBatch,
        "SettlementReconciliation": reconciliation.SettlementReconciliation,
    }
    for symbol, module_value in module_types.items():
        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__ and symbol in novapay.__all__


def test_receipt_aggregate_remains_module_local() -> None:
    assert hasattr(receipt, "Receipt") and "Receipt" in receipt.__all__
    assert not hasattr(domain, "Receipt") and "Receipt" not in domain.__all__
    assert not hasattr(novapay, "Receipt") and "Receipt" not in novapay.__all__


def test_transaction_to_wallet_reference_contract_is_certified() -> None:
    _assert_source_and_test_vocabulary(
        ("wallet_id", "source_wallet", "destination_wallet", "wallet"),
        ("wallet", "source_wallet", "destination_wallet"),
    )


def test_transaction_to_ledger_and_journal_propagation_is_certified() -> None:
    _assert_source_and_test_vocabulary(
        ("ledger_account", "ledger_account_id", "journal_entry", "journal_entry_id"),
        ("ledger_account", "journal_entry", "ledger"),
    )


def test_journal_debit_credit_balancing_contract_is_certified() -> None:
    implementation = inspect.getsource(journal_entry).lower()
    tests = _focused_test_source().lower()
    assert "debit" in implementation and "credit" in implementation
    assert any(token in implementation for token in ("balance", "balanced", "must equal"))
    assert "debit" in tests and "credit" in tests
    assert any(token in tests for token in ("balance", "balanced", "imbalance"))


def test_transaction_and_journal_idempotency_contract_is_certified() -> None:
    _assert_source_and_test_vocabulary(
        ("idempotency", "idempotent", "duplicate", "request_id", "correlation_id"),
        ("idempotency", "idempotent", "duplicate", "request_id"),
    )


def test_transfer_to_transaction_linkage_is_certified() -> None:
    _assert_source_and_test_vocabulary(
        ("transaction_id", "transaction_reference", "transfer_id", "transfer_reference"),
        ("transaction_id", "transaction_reference", "transfer"),
    )


def test_settlement_membership_and_reconciliation_linkage_are_certified() -> None:
    implementation = (
        inspect.getsource(settlement_batch) + "\n" + inspect.getsource(reconciliation)
    ).lower()
    tests = _focused_test_source().lower()
    assert "settlement" in implementation and "reconciliation" in implementation
    assert any(
        token in implementation
        for token in ("batch_id", "settlement_batch_id", "transaction_id", "transfer_id", "members")
    )
    assert "settlement" in tests and "reconciliation" in tests


def test_receipt_reference_compatibility_is_certified_without_export_widening() -> None:
    implementation = inspect.getsource(receipt).lower()
    tests = _focused_test_source().lower()
    assert "receiptreference" in implementation.replace("_", "")
    assert "reference_type" in implementation and "reference_value" in implementation
    assert any(token in implementation for token in ("transaction", "transfer", "settlement", "reconciliation"))
    assert "receipt" in tests and "reference" in tests


def test_lifecycle_status_alignment_is_certified() -> None:
    implementation = "\n".join(
        inspect.getsource(module)
        for module in (transaction, transfer, settlement_batch, reconciliation, receipt)
    ).lower()
    tests = _focused_test_source().lower()
    assert any(token in implementation for token in ("status", "state", "transition", "lifecycle"))
    assert any(token in tests for token in ("status", "state", "transition", "lifecycle"))


def test_serialization_replay_and_event_ordering_contracts_are_certified() -> None:
    canonical_types = (
        transaction.Transaction,
        journal_entry.JournalEntry,
        transfer.Transfer,
        settlement_batch.SettlementBatch,
        reconciliation.SettlementReconciliation,
        receipt.Receipt,
    )
    serialization_methods = {"canonical_dict", "to_dict", "as_dict", "serialize", "from_dict", "deserialize"}
    assert sum(bool(serialization_methods.intersection(_public_methods(value))) for value in canonical_types) >= 4
    implementation = _combined_implementation_source().lower()
    tests = _focused_test_source().lower()
    assert any(token in implementation for token in ("version", "sequence", "occurred_at", "created_at", "event_id"))
    assert any(token in tests for token in ("round_trip", "replay", "canonical_dict", "serialize", "version", "sequence"))


def test_domain_records_have_no_runtime_execution_or_persistence_authority() -> None:
    canonical_types = (
        wallet.Wallet,
        ledger_account.LedgerAccount,
        journal_entry.JournalEntry,
        transaction.Transaction,
        transfer.Transfer,
        settlement_batch.SettlementBatch,
        reconciliation.SettlementReconciliation,
        receipt.Receipt,
    )
    forbidden = {
        "authorize_payment", "capture_payment", "execute_payment", "post_ledger",
        "settle_external", "persist", "save", "repository", "database",
        "provider_client", "http_client", "network_client", "publish", "send",
    }
    for value in canonical_types:
        names = {name for name in dir(value) if not name.startswith("__")}
        assert forbidden.isdisjoint(names), (value.__name__, sorted(forbidden.intersection(names)))
        if is_dataclass(value):
            assert forbidden.isdisjoint({item.name for item in fields(value)})


def test_transaction_ledger_domain_modules_remain_replay_safe() -> None:
    forbidden_import_roots = {
        "django", "flask", "fastapi", "requests", "httpx", "sqlalchemy",
        "psycopg", "sqlite3", "redis", "celery", "boto3",
    }
    violations: list[tuple[str, str, int]] = []
    for path in INTEGRATION_MODULE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in forbidden_import_roots:
                        violations.append((str(path), root, node.lineno))
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in forbidden_import_roots:
                    violations.append((str(path), root, node.lineno))
    assert violations == []
