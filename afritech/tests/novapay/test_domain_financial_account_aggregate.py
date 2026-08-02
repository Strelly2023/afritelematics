from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.customer import CustomerId
from afritech.novapay.domain.financial_account import (
    FinancialAccount,
    FinancialAccountId,
    FinancialAccountMetadata,
    FinancialAccountName,
    FinancialAccountPurpose,
    FinancialAccountRestrictions,
    FinancialAccountStatus,
    FinancialAccountTerms,
    FinancialAccountType,
)
from afritech.novapay.domain.ledger_account import (
    LedgerAccountId,
)
from afritech.novapay.domain.money import Currency
from afritech.novapay.domain.wallet import WalletId


def aud_currency() -> Currency:
    """Construct AUD through the canonical Currency API."""

    return Currency.of("AUD")


NOW = datetime(2026, 8, 2, 8, 0, tzinfo=timezone.utc)


def current_account(
    **overrides: object,
) -> FinancialAccount:
    values: dict[str, object] = {
        "account_id": FinancialAccountId(
            "financial-account-001"
        ),
        "customer_id": CustomerId("customer-001"),
        "tenant_id": "tenant-001",
        "account_type": FinancialAccountType.CURRENT,
        "purpose": (
            FinancialAccountPurpose.EVERYDAY_PAYMENTS
        ),
        "status": FinancialAccountStatus.PENDING,
        "currency": aud_currency(),
        "name": FinancialAccountName(
            "NovaPay Everyday Account"
        ),
        "wallet_id": WalletId("wallet-001"),
        "ledger_account_id": None,
        "terms": FinancialAccountTerms(
            overdraft_limit="500.00"
        ),
        "restrictions": FinancialAccountRestrictions(),
        "metadata": FinancialAccountMetadata(
            {"product_code": "CUR-001"}
        ),
        "created_at": NOW,
        "updated_at": NOW,
        "version": 1,
    }
    values.update(overrides)

    return FinancialAccount(**values)  # type: ignore[arg-type]


def test_create_current_financial_account() -> None:
    account = FinancialAccount.create(
        account_id=" financial-account-001 ",
        customer_id=" customer-001 ",
        tenant_id=" tenant-001 ",
        account_type=" CURRENT ",
        purpose=" EVERYDAY_PAYMENTS ",
        currency=aud_currency(),
        name=FinancialAccountName(
            " NovaPay   Everyday Account "
        ),
        wallet_id=" wallet-001 ",
        terms={
            "overdraft_limit": "500.00",
        },
        metadata={
            " product_code ": "CUR-001",
        },
        occurred_at=NOW,
    )

    assert account.account_id == FinancialAccountId(
        "financial-account-001"
    )
    assert account.customer_id == CustomerId(
        "customer-001"
    )
    assert account.tenant_id == "tenant-001"
    assert account.account_type is FinancialAccountType.CURRENT
    assert account.purpose is (
        FinancialAccountPurpose.EVERYDAY_PAYMENTS
    )
    assert account.status is FinancialAccountStatus.PENDING
    assert account.currency == aud_currency()
    assert account.wallet_id == WalletId("wallet-001")
    assert account.version == 1
    assert account.created_at == NOW
    assert account.updated_at == NOW


def test_financial_account_normalizes_references() -> None:
    account = current_account(
        account_id=" financial-account-001 ",
        customer_id=" customer-001 ",
        wallet_id=" wallet-001 ",
    )

    assert account.account_id.value == "financial-account-001"
    assert account.customer_id.value == "customer-001"
    assert account.wallet_id == WalletId("wallet-001")


def test_financial_account_is_immutable() -> None:
    account = current_account()

    with pytest.raises(FrozenInstanceError):
        account.status = (  # type: ignore[misc]
            FinancialAccountStatus.ACTIVE
        )


def test_financial_account_uses_slots() -> None:
    assert not hasattr(current_account(), "__dict__")


def test_financial_account_requires_currency() -> None:
    with pytest.raises(
        TypeError,
        match="currency must be a Currency",
    ):
        current_account(
            currency="AUD",
        )


def test_financial_account_requires_name_value_object() -> None:
    with pytest.raises(
        TypeError,
        match="FinancialAccountName",
    ):
        current_account(
            name="NovaPay Account",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "account_id",
        "customer_id",
        "tenant_id",
    ],
)
def test_financial_account_requires_identifiers(
    field_name: str,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        current_account(
            **{field_name: " "}
        )


@pytest.mark.parametrize(
    "account_type",
    [
        FinancialAccountType.CURRENT,
        FinancialAccountType.SAVINGS,
        FinancialAccountType.MERCHANT,
        FinancialAccountType.AGENT_FLOAT,
        FinancialAccountType.PAYROLL,
        FinancialAccountType.BENEFIT,
    ],
)
def test_wallet_backed_types_require_wallet(
    account_type: FinancialAccountType,
) -> None:
    purpose_map = {
        FinancialAccountType.CURRENT: (
            FinancialAccountPurpose.EVERYDAY_PAYMENTS
        ),
        FinancialAccountType.SAVINGS: (
            FinancialAccountPurpose.SAVINGS
        ),
        FinancialAccountType.MERCHANT: (
            FinancialAccountPurpose.MERCHANT_COLLECTIONS
        ),
        FinancialAccountType.AGENT_FLOAT: (
            FinancialAccountPurpose.AGENT_LIQUIDITY
        ),
        FinancialAccountType.PAYROLL: (
            FinancialAccountPurpose.PAYROLL
        ),
        FinancialAccountType.BENEFIT: (
            FinancialAccountPurpose.BENEFIT_DISBURSEMENT
        ),
    }

    terms = (
        FinancialAccountTerms(
            interest_rate_percent="1"
        )
        if account_type is FinancialAccountType.SAVINGS
        else FinancialAccountTerms()
    )

    with pytest.raises(
        ValueError,
        match="requires a wallet id",
    ):
        FinancialAccount.create(
            account_id=f"{account_type.value}-001",
            customer_id="customer-001",
            tenant_id="tenant-001",
            account_type=account_type,
            purpose=purpose_map[account_type],
            currency=aud_currency(),
            name=FinancialAccountName(
                f"NovaPay {account_type.value}"
            ),
            terms=terms,
            occurred_at=NOW,
        )


@pytest.mark.parametrize(
    "account_type",
    [
        FinancialAccountType.SETTLEMENT,
        FinancialAccountType.TREASURY,
        FinancialAccountType.ESCROW,
        FinancialAccountType.CLEARING,
        FinancialAccountType.LOAN,
        FinancialAccountType.INVESTMENT,
    ],
)
def test_ledger_backed_types_require_ledger_account(
    account_type: FinancialAccountType,
) -> None:
    purpose_map = {
        FinancialAccountType.SETTLEMENT: (
            FinancialAccountPurpose.SETTLEMENT
        ),
        FinancialAccountType.TREASURY: (
            FinancialAccountPurpose.TREASURY
        ),
        FinancialAccountType.ESCROW: (
            FinancialAccountPurpose.ESCROW
        ),
        FinancialAccountType.CLEARING: (
            FinancialAccountPurpose.CLEARING
        ),
        FinancialAccountType.LOAN: (
            FinancialAccountPurpose.CREDIT
        ),
        FinancialAccountType.INVESTMENT: (
            FinancialAccountPurpose.INVESTMENT
        ),
    }

    with pytest.raises(
        ValueError,
        match="requires a ledger account id",
    ):
        FinancialAccount.create(
            account_id=f"{account_type.value}-001",
            customer_id="customer-001",
            tenant_id="tenant-001",
            account_type=account_type,
            purpose=purpose_map[account_type],
            currency=aud_currency(),
            name=FinancialAccountName(
                f"NovaPay {account_type.value}"
            ),
            occurred_at=NOW,
        )


@pytest.mark.parametrize(
    ("account_type", "purpose"),
    [
        (
            FinancialAccountType.CURRENT,
            FinancialAccountPurpose.SAVINGS,
        ),
        (
            FinancialAccountType.SAVINGS,
            FinancialAccountPurpose.EVERYDAY_PAYMENTS,
        ),
        (
            FinancialAccountType.MERCHANT,
            FinancialAccountPurpose.AGENT_LIQUIDITY,
        ),
        (
            FinancialAccountType.TREASURY,
            FinancialAccountPurpose.SETTLEMENT,
        ),
    ],
)
def test_account_type_and_purpose_must_match(
    account_type: FinancialAccountType,
    purpose: FinancialAccountPurpose,
) -> None:
    with pytest.raises(
        ValueError,
        match="purpose is incompatible",
    ):
        FinancialAccount.create(
            account_id="financial-account-001",
            customer_id="customer-001",
            tenant_id="tenant-001",
            account_type=account_type,
            purpose=purpose,
            currency=aud_currency(),
            name=FinancialAccountName("NovaPay Account"),
            wallet_id="wallet-001",
            ledger_account_id="ledger-account-001",
            terms=FinancialAccountTerms(
                interest_rate_percent="1"
            ),
            occurred_at=NOW,
        )


def test_only_current_account_may_have_overdraft() -> None:
    with pytest.raises(
        ValueError,
        match="only current financial accounts",
    ):
        FinancialAccount.create(
            account_id="savings-001",
            customer_id="customer-001",
            tenant_id="tenant-001",
            account_type=FinancialAccountType.SAVINGS,
            purpose=FinancialAccountPurpose.SAVINGS,
            currency=aud_currency(),
            name=FinancialAccountName("NovaPay Savings"),
            wallet_id="wallet-001",
            terms=FinancialAccountTerms(
                overdraft_limit="1",
                interest_rate_percent="2",
            ),
            occurred_at=NOW,
        )


def test_savings_requires_interest_or_notice_period() -> None:
    with pytest.raises(
        ValueError,
        match="requires an interest rate or notice period",
    ):
        FinancialAccount.create(
            account_id="savings-001",
            customer_id="customer-001",
            tenant_id="tenant-001",
            account_type=FinancialAccountType.SAVINGS,
            purpose=FinancialAccountPurpose.SAVINGS,
            currency=aud_currency(),
            name=FinancialAccountName("NovaPay Savings"),
            wallet_id="wallet-001",
            occurred_at=NOW,
        )


def test_savings_accepts_interest_rate() -> None:
    account = FinancialAccount.create(
        account_id="savings-001",
        customer_id="customer-001",
        tenant_id="tenant-001",
        account_type=FinancialAccountType.SAVINGS,
        purpose=FinancialAccountPurpose.SAVINGS,
        currency=aud_currency(),
        name=FinancialAccountName("NovaPay Savings"),
        wallet_id="wallet-001",
        terms=FinancialAccountTerms(
            interest_rate_percent="3.5"
        ),
        occurred_at=NOW,
    )

    assert account.terms.interest_rate_percent == Decimal(
        "3.5"
    )


def test_closed_account_requires_full_restriction() -> None:
    with pytest.raises(
        ValueError,
        match="must block both debits and credits",
    ):
        current_account(
            status=FinancialAccountStatus.CLOSED,
        )


def test_closed_account_accepts_full_restriction() -> None:
    account = current_account(
        status=FinancialAccountStatus.CLOSED,
        restrictions=FinancialAccountRestrictions(
            debit_blocked=True,
            credit_blocked=True,
        ),
    )

    assert account.status is FinancialAccountStatus.CLOSED
    assert account.restrictions.fully_blocked is True


def test_financial_account_normalizes_terms_mapping() -> None:
    account = current_account(
        terms={
            "overdraft_limit": "750.00",
        },
    )

    assert account.terms.overdraft_limit == Decimal(
        "750.00"
    )


def test_financial_account_normalizes_restrictions_mapping() -> None:
    account = current_account(
        restrictions={
            "cash_withdrawal_blocked": True,
            "allowed_channels": ["mobile"],
        },
    )

    assert account.restrictions.cash_withdrawal_blocked is True
    assert account.restrictions.allowed_channels == (
        "mobile",
    )


def test_financial_account_rejects_invalid_terms() -> None:
    with pytest.raises(
        TypeError,
        match="terms must be",
    ):
        current_account(
            terms="invalid",
        )


def test_financial_account_rejects_invalid_restrictions() -> None:
    with pytest.raises(
        TypeError,
        match="restrictions must be",
    ):
        current_account(
            restrictions="invalid",
        )


def test_financial_account_metadata_rejects_sensitive_data() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        current_account(
            metadata={
                "access_token": "secret",
            }
        )


def test_financial_account_timestamp_normalization() -> None:
    local_timezone = timezone(timedelta(hours=10))
    timestamp = datetime(
        2026,
        8,
        2,
        18,
        0,
        tzinfo=local_timezone,
    )

    account = current_account(
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert account.created_at.tzinfo is timezone.utc
    assert account.created_at.hour == 8


def test_financial_account_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        current_account(
            created_at=datetime(2026, 8, 2, 8, 0),
        )


def test_financial_account_rejects_updated_before_created() -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        current_account(
            updated_at=NOW - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_financial_account_rejects_invalid_version(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        current_account(version=value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1",
        1.0,
        None,
    ],
)
def test_financial_account_rejects_non_integer_version(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        current_account(version=value)


def test_financial_account_canonical_dict() -> None:
    account = current_account()

    payload = account.canonical_dict()

    assert list(payload) == [
        "account_id",
        "customer_id",
        "tenant_id",
        "account_type",
        "purpose",
        "status",
        "currency",
        "name",
        "wallet_id",
        "ledger_account_id",
        "terms",
        "restrictions",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]
    assert payload["account_id"] == "financial-account-001"
    assert payload["customer_id"] == "customer-001"
    assert payload["tenant_id"] == "tenant-001"
    assert payload["account_type"] == "current"
    assert payload["purpose"] == "everyday_payments"
    assert payload["status"] == "pending"
    assert payload["currency"] == "AUD"
    assert payload["wallet_id"] == "wallet-001"
    assert payload["ledger_account_id"] is None
    assert payload["version"] == 1


def test_financial_account_canonical_dict_is_fresh() -> None:
    account = current_account()

    first = account.canonical_dict()
    second = account.canonical_dict()

    assert first == second
    assert first is not second
    assert first["terms"] is not second["terms"]
    assert first["metadata"] is not second["metadata"]


def test_financial_account_contains_no_balance_authority() -> None:
    account = current_account()

    for field_name in (
        "balance",
        "available_balance",
        "current_balance",
        "ledger_balance",
        "journal_entries",
        "transactions",
    ):
        assert not hasattr(account, field_name)


def test_module_contract_includes_aggregate() -> None:
    from afritech.novapay.domain import financial_account

    assert financial_account.__all__ == [
        "FinancialAccount",
        "FinancialAccountId",
        "FinancialAccountMetadata",
        "FinancialAccountName",
        "FinancialAccountPurpose",
        "FinancialAccountRestrictions",
        "FinancialAccountStatus",
        "FinancialAccountTerms",
        "FinancialAccountType",
    ]
