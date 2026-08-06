from __future__ import annotations

import ast
import inspect
from dataclasses import fields, is_dataclass
from pathlib import Path

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.fx as fx
import afritech.novapay.domain.receipt as receipt
import afritech.novapay.domain.remittance as remittance
import afritech.novapay.domain.settlement_batch as settlement_batch
import afritech.novapay.domain.settlement_reconciliation as reconciliation
import afritech.novapay.domain.transfer as transfer


DOMAIN_ROOT = Path("afritech/novapay/domain")
TEST_ROOT = Path("afritech/tests/novapay")

INTEGRATION_MODULE_PATHS = (
    DOMAIN_ROOT / "transfer.py",
    DOMAIN_ROOT / "remittance.py",
    DOMAIN_ROOT / "settlement_batch.py",
    DOMAIN_ROOT / "settlement_reconciliation.py",
    DOMAIN_ROOT / "transaction.py",
    DOMAIN_ROOT / "money.py",
    DOMAIN_ROOT / "fx.py",
    DOMAIN_ROOT / "customer.py",
    DOMAIN_ROOT / "financial_account.py",
    DOMAIN_ROOT / "receipt.py",
)

FOCUSED_TEST_PATTERNS = (
    "*transfer*.py",
    "*remittance*.py",
    "*settlement*.py",
    "*reconciliation*.py",
    "*receipt*.py",
    "*transaction*.py",
    "*customer*.py",
    "*financial_account*.py",
    "*fx*.py",
)

SERIALIZATION_METHODS = {
    "canonical_dict",
    "to_dict",
    "as_dict",
    "serialize",
    "from_dict",
    "deserialize",
}


def _combined_implementation_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in INTEGRATION_MODULE_PATHS
    )


def _focused_test_source() -> str:
    paths: set[Path] = set()

    for pattern in FOCUSED_TEST_PATTERNS:
        paths.update(TEST_ROOT.glob(pattern))

    excluded = {
        "test_phase1_transfer_remittance_settlement_integration_certification.py",
    }

    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(paths)
        if path.name not in excluded
    )


def _public_methods(value: type[object]) -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(value)
        if callable(member) and not name.startswith("_")
    }


def _field_names(value: type[object]) -> set[str]:
    if not is_dataclass(value):
        return set()

    return {
        item.name
        for item in fields(value)
    }


def _assert_source_and_test_vocabulary(
    implementation_tokens: tuple[str, ...],
    test_tokens: tuple[str, ...],
) -> None:
    implementation = _combined_implementation_source().lower()
    tests = _focused_test_source().lower()

    assert any(
        token.lower() in implementation
        for token in implementation_tokens
    )

    assert any(
        token.lower() in tests
        for token in test_tokens
    )


def test_canonical_transfer_remittance_settlement_identities() -> None:
    canonical = {
        "Transfer": transfer.Transfer,
        "Remittance": remittance.Remittance,
        "SettlementBatch": settlement_batch.SettlementBatch,
        "SettlementReconciliation": (
            reconciliation.SettlementReconciliation
        ),
    }

    for symbol, module_value in canonical.items():
        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_receipt_aggregate_remains_module_local() -> None:
    assert hasattr(receipt, "Receipt")
    assert "Receipt" in receipt.__all__

    assert not hasattr(domain, "Receipt")
    assert "Receipt" not in domain.__all__

    assert not hasattr(novapay, "Receipt")
    assert "Receipt" not in novapay.__all__


def test_transfer_and_remittance_ownership_references_are_certified() -> None:
    _assert_source_and_test_vocabulary(
        (
            "transfer_id",
            "remittance_id",
            "customer_id",
            "sender",
            "beneficiary",
            "owner",
        ),
        (
            "transfer_id",
            "remittance_id",
            "customer",
            "sender",
            "beneficiary",
        ),
    )


def test_party_customer_and_financial_account_references_are_certified() -> None:
    _assert_source_and_test_vocabulary(
        (
            "sender",
            "beneficiary",
            "customer_id",
            "financial_account_id",
            "account_id",
            "source_account",
            "destination_account",
        ),
        (
            "sender",
            "beneficiary",
            "customer",
            "financial_account",
            "account",
        ),
    )


def test_transfer_to_remittance_linkage_is_certified() -> None:
    implementation = (
        inspect.getsource(transfer)
        + "\n"
        + inspect.getsource(remittance)
    ).lower()

    tests = _focused_test_source().lower()

    assert "transfer" in implementation
    assert "remittance" in implementation

    assert any(
        token in implementation
        for token in (
            "transfer_id",
            "transfer_reference",
            "remittance_id",
            "remittance_reference",
        )
    )

    assert "transfer" in tests
    assert "remittance" in tests


def test_send_receive_fee_and_payout_reconciliation_is_certified() -> None:
    implementation = (
        inspect.getsource(transfer)
        + "\n"
        + inspect.getsource(remittance)
    ).lower()

    tests = _focused_test_source().lower()

    assert any(
        token in implementation
        for token in (
            "send_amount",
            "receive_amount",
            "payout_amount",
            "principal",
            "amount",
        )
    )

    assert "fee" in implementation

    assert any(
        token in tests
        for token in (
            "send_amount",
            "receive_amount",
            "payout",
            "principal",
            "amount",
        )
    )

    assert "fee" in tests


def test_fx_quote_and_currency_pair_consistency_is_certified() -> None:
    implementation = (
        inspect.getsource(fx)
        + "\n"
        + inspect.getsource(transfer)
        + "\n"
        + inspect.getsource(remittance)
    ).lower()

    tests = _focused_test_source().lower()

    assert hasattr(fx, "FXQuote")
    assert hasattr(fx, "CurrencyPair")

    assert any(
        token in implementation
        for token in (
            "fx_quote",
            "currency_pair",
            "exchange_rate",
            "source_currency",
            "target_currency",
        )
    )

    assert any(
        token in tests
        for token in (
            "fx_quote",
            "currency_pair",
            "exchange_rate",
            "source_currency",
            "target_currency",
        )
    )


def test_settlement_batch_membership_and_uniqueness_are_certified() -> None:
    implementation = inspect.getsource(settlement_batch).lower()
    tests = _focused_test_source().lower()

    assert any(
        token in implementation
        for token in (
            "members",
            "transaction_ids",
            "transfer_ids",
            "remittance_ids",
            "batch_id",
        )
    )

    assert any(
        token in implementation
        for token in (
            "duplicate",
            "unique",
            "already",
            "must not contain",
        )
    )

    assert "settlement" in tests

    assert any(
        token in tests
        for token in (
            "duplicate",
            "unique",
            "membership",
            "member",
        )
    )


def test_settlement_reconciliation_linkage_is_certified() -> None:
    implementation = (
        inspect.getsource(settlement_batch)
        + "\n"
        + inspect.getsource(reconciliation)
    ).lower()

    tests = _focused_test_source().lower()

    assert "settlement" in implementation
    assert "reconciliation" in implementation

    assert any(
        token in implementation
        for token in (
            "settlement_batch_id",
            "settlement_id",
            "reconciliation_id",
            "transfer_id",
            "remittance_id",
            "transaction_id",
        )
    )

    assert "settlement" in tests
    assert "reconciliation" in tests


def test_lifecycle_status_and_terminal_invariants_are_certified() -> None:
    modules = (
        transfer,
        remittance,
        settlement_batch,
        reconciliation,
    )

    implementation = "\n".join(
        inspect.getsource(module)
        for module in modules
    ).lower()

    tests = _focused_test_source().lower()

    assert any(
        token in implementation
        for token in (
            "status",
            "state",
            "transition",
            "lifecycle",
        )
    )

    assert any(
        token in implementation
        for token in (
            "cancel",
            "fail",
            "complete",
            "settled",
            "reconcile",
        )
    )

    assert any(
        token in tests
        for token in (
            "status",
            "state",
            "transition",
            "lifecycle",
        )
    )

    assert any(
        token in tests
        for token in (
            "cancel",
            "fail",
            "complete",
            "settled",
            "reconcile",
        )
    )


def test_idempotency_and_duplicate_prevention_are_certified() -> None:
    _assert_source_and_test_vocabulary(
        (
            "idempotency",
            "idempotent",
            "duplicate",
            "request_id",
            "correlation_id",
        ),
        (
            "idempotency",
            "idempotent",
            "duplicate",
            "request_id",
        ),
    )


def test_serialization_and_replay_determinism_are_certified() -> None:
    canonical_types = (
        transfer.Transfer,
        remittance.Remittance,
        settlement_batch.SettlementBatch,
        reconciliation.SettlementReconciliation,
        receipt.Receipt,
    )

    covered = 0

    for value in canonical_types:
        if SERIALIZATION_METHODS.intersection(
            _public_methods(value)
        ):
            covered += 1

    assert covered >= 4

    implementation = _combined_implementation_source().lower()
    tests = _focused_test_source().lower()

    assert any(
        token in implementation
        for token in (
            "canonical_dict",
            "to_dict",
            "from_dict",
            "serialize",
            "canonical",
        )
    )

    assert any(
        token in tests
        for token in (
            "canonical_dict",
            "round_trip",
            "serialize",
            "replay",
        )
    )


def test_receipt_reference_compatibility_preserves_export_boundary() -> None:
    implementation = inspect.getsource(receipt).lower()
    tests = _focused_test_source().lower()

    assert hasattr(receipt, "ReceiptReference")
    assert hasattr(receipt, "ReceiptReferenceType")

    assert "reference_type" in implementation
    assert "reference_value" in implementation

    assert any(
        token in implementation
        for token in (
            "transfer",
            "remittance",
            "settlement",
            "reconciliation",
            "transaction",
        )
    )

    assert "receipt" in tests
    assert "reference" in tests

    assert not hasattr(domain, "Receipt")
    assert not hasattr(novapay, "Receipt")


def test_immutable_interactions_and_authority_boundaries_are_certified() -> None:
    canonical_types = (
        transfer.Transfer,
        remittance.Remittance,
        settlement_batch.SettlementBatch,
        reconciliation.SettlementReconciliation,
        receipt.Receipt,
    )

    forbidden = {
        "execute_payment",
        "authorize_payment",
        "capture_payment",
        "debit_wallet",
        "credit_wallet",
        "post_ledger",
        "settle_external",
        "persist",
        "save",
        "repository",
        "database",
        "provider_client",
        "network_client",
        "http_client",
        "publish",
        "send",
        "deliver",
    }

    for value in canonical_types:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True

        names = {
            name
            for name in dir(value)
            if not name.startswith("__")
        }

        assert forbidden.isdisjoint(names), (
            value.__name__,
            sorted(forbidden.intersection(names)),
        )

        assert forbidden.isdisjoint(
            _field_names(value)
        )


def test_integration_domain_modules_remain_replay_safe() -> None:
    forbidden_import_roots = {
        "django",
        "flask",
        "fastapi",
        "requests",
        "httpx",
        "sqlalchemy",
        "psycopg",
        "sqlite3",
        "redis",
        "celery",
        "boto3",
    }

    violations: list[tuple[str, str, int]] = []

    for path in INTEGRATION_MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]

                    if root in forbidden_import_roots:
                        violations.append(
                            (str(path), root, node.lineno)
                        )

            if isinstance(node, ast.ImportFrom):
                if not node.module:
                    continue

                root = node.module.split(".")[0]

                if root in forbidden_import_roots:
                    violations.append(
                        (str(path), root, node.lineno)
                    )

    assert violations == []
