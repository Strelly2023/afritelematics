from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.financial_account import (
    FinancialAccount,
    FinancialAccountMetadata,
    FinancialAccountName,
    FinancialAccountPurpose,
    FinancialAccountRestrictions,
    FinancialAccountStatus,
    FinancialAccountTerms,
    FinancialAccountType,
)
from afritech.novapay.domain.money import Currency
from afritech.novapay.domain.wallet import WalletId
from afritech.novapay.domain.ledger_account import (
    LedgerAccountId,
)


NOW = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=5)


def aud_currency() -> Currency:
    return Currency.of("AUD")


def pending_account() -> FinancialAccount:
    return FinancialAccount.create(
        account_id="financial-account-001",
        customer_id="customer-001",
        tenant_id="tenant-001",
        account_type=FinancialAccountType.CURRENT,
        purpose=FinancialAccountPurpose.EVERYDAY_PAYMENTS,
        currency=aud_currency(),
        name=FinancialAccountName(
            "NovaPay Everyday Account"
        ),
        wallet_id="wallet-001",
        terms=FinancialAccountTerms(
            overdraft_limit="500"
        ),
        metadata={
            "product_code": "CUR-001",
        },
        occurred_at=NOW,
    )


def account_with_status(
    status: FinancialAccountStatus,
) -> FinancialAccount:
    account = pending_account()

    if status is FinancialAccountStatus.PENDING:
        return account

    active = account.activate(
        occurred_at=LATER
    )

    if status is FinancialAccountStatus.ACTIVE:
        return active

    if status is FinancialAccountStatus.RESTRICTED:
        return active.restrict(
            reason="risk review",
            occurred_at=LATER + timedelta(minutes=1),
        )

    if status is FinancialAccountStatus.SUSPENDED:
        return active.suspend(
            reason="security review",
            occurred_at=LATER + timedelta(minutes=1),
        )

    if status is FinancialAccountStatus.DORMANT:
        return active.mark_dormant(
            reason="inactivity",
            occurred_at=LATER + timedelta(minutes=1),
        )

    return active.close(
        reason="account closed",
        occurred_at=LATER + timedelta(minutes=1),
    )


def assert_identity_preserved(
    before: FinancialAccount,
    after: FinancialAccount,
) -> None:
    assert after.account_id == before.account_id
    assert after.customer_id == before.customer_id
    assert after.tenant_id == before.tenant_id
    assert after.account_type is before.account_type
    assert after.purpose is before.purpose
    assert after.currency == before.currency
    assert after.created_at == before.created_at


def assert_new_version(
    before: FinancialAccount,
    after: FinancialAccount,
    *,
    occurred_at: datetime,
) -> None:
    assert after is not before
    assert after.version == before.version + 1
    assert after.updated_at == occurred_at
    assert_identity_preserved(before, after)


def test_activate_pending_account() -> None:
    original = pending_account()

    active = original.activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    assert original.status is FinancialAccountStatus.PENDING
    assert active.status is FinancialAccountStatus.ACTIVE
    assert active.metadata.values["lifecycle_action"] == (
        "activate"
    )
    assert active.metadata.values["lifecycle_reason"] == (
        "verification complete"
    )
    assert_new_version(
        original,
        active,
        occurred_at=LATER,
    )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.ACTIVE,
        FinancialAccountStatus.RESTRICTED,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
        FinancialAccountStatus.CLOSED,
    ],
)
def test_activate_rejects_non_pending(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)

    with pytest.raises(ValueError):
        account.activate(
            occurred_at=account.updated_at,
        )


def test_restrict_active_account() -> None:
    active = pending_account().activate(
        occurred_at=LATER
    )
    occurred_at = LATER + timedelta(minutes=1)

    restricted = active.restrict(
        reason="risk review",
        occurred_at=occurred_at,
    )

    assert restricted.status is (
        FinancialAccountStatus.RESTRICTED
    )
    assert restricted.restrictions.debit_blocked is True
    assert restricted.restrictions.credit_blocked is False
    assert_new_version(
        active,
        restricted,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.PENDING,
        FinancialAccountStatus.RESTRICTED,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
        FinancialAccountStatus.CLOSED,
    ],
)
def test_restrict_rejects_invalid_status(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)

    with pytest.raises(ValueError):
        account.restrict(
            reason="review",
            occurred_at=account.updated_at,
        )


@pytest.mark.parametrize(
    "starting_status",
    [
        FinancialAccountStatus.ACTIVE,
        FinancialAccountStatus.RESTRICTED,
    ],
)
def test_suspend_allowed_statuses(
    starting_status: FinancialAccountStatus,
) -> None:
    account = account_with_status(starting_status)
    occurred_at = account.updated_at + timedelta(minutes=1)

    suspended = account.suspend(
        reason="security review",
        occurred_at=occurred_at,
    )

    assert suspended.status is FinancialAccountStatus.SUSPENDED
    assert suspended.restrictions.fully_blocked is True
    assert_new_version(
        account,
        suspended,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.PENDING,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
        FinancialAccountStatus.CLOSED,
    ],
)
def test_suspend_rejects_invalid_status(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)

    with pytest.raises(ValueError):
        account.suspend(
            reason="review",
            occurred_at=account.updated_at,
        )


def test_mark_dormant_active_account() -> None:
    active = pending_account().activate(
        occurred_at=LATER
    )
    occurred_at = LATER + timedelta(minutes=1)

    dormant = active.mark_dormant(
        reason="inactivity",
        occurred_at=occurred_at,
    )

    assert dormant.status is FinancialAccountStatus.DORMANT
    assert dormant.restrictions.debit_blocked is True
    assert dormant.restrictions.credit_blocked is False
    assert_new_version(
        active,
        dormant,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.PENDING,
        FinancialAccountStatus.RESTRICTED,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
        FinancialAccountStatus.CLOSED,
    ],
)
def test_mark_dormant_rejects_invalid_status(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)

    with pytest.raises(ValueError):
        account.mark_dormant(
            occurred_at=account.updated_at,
        )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.RESTRICTED,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
    ],
)
def test_reactivate_returns_account_to_active(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)
    occurred_at = account.updated_at + timedelta(minutes=1)

    active = account.reactivate(
        reason="review complete",
        occurred_at=occurred_at,
    )

    assert active.status is FinancialAccountStatus.ACTIVE
    assert active.restrictions.debit_blocked is False
    assert active.restrictions.credit_blocked is False
    assert_new_version(
        account,
        active,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.PENDING,
        FinancialAccountStatus.ACTIVE,
        FinancialAccountStatus.CLOSED,
    ],
)
def test_reactivate_rejects_invalid_status(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)

    with pytest.raises(ValueError):
        account.reactivate(
            occurred_at=account.updated_at,
        )


@pytest.mark.parametrize(
    "status",
    [
        FinancialAccountStatus.PENDING,
        FinancialAccountStatus.ACTIVE,
        FinancialAccountStatus.RESTRICTED,
        FinancialAccountStatus.SUSPENDED,
        FinancialAccountStatus.DORMANT,
    ],
)
def test_close_accepts_every_non_closed_status(
    status: FinancialAccountStatus,
) -> None:
    account = account_with_status(status)
    occurred_at = account.updated_at + timedelta(minutes=1)

    closed = account.close(
        reason="customer request",
        occurred_at=occurred_at,
    )

    assert closed.status is FinancialAccountStatus.CLOSED
    assert closed.restrictions.debit_blocked is True
    assert closed.restrictions.credit_blocked is True
    assert closed.restrictions.cash_withdrawal_blocked is True
    assert (
        closed.restrictions.international_transfer_blocked
        is True
    )
    assert_new_version(
        account,
        closed,
        occurred_at=occurred_at,
    )


def test_closed_account_is_terminal() -> None:
    closed = account_with_status(
        FinancialAccountStatus.CLOSED
    )

    operations = (
        lambda: closed.activate(
            occurred_at=closed.updated_at,
        ),
        lambda: closed.restrict(
            reason="review",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.suspend(
            reason="review",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.mark_dormant(
            occurred_at=closed.updated_at,
        ),
        lambda: closed.reactivate(
            occurred_at=closed.updated_at,
        ),
        lambda: closed.close(
            reason="again",
            occurred_at=closed.updated_at,
        ),
        lambda: closed.rename(
            FinancialAccountName("Changed"),
            occurred_at=closed.updated_at,
        ),
        lambda: closed.change_terms(
            FinancialAccountTerms(
                overdraft_limit="100"
            ),
            occurred_at=closed.updated_at,
        ),
        lambda: closed.update_metadata(
            {"source": "closed"},
            occurred_at=closed.updated_at,
        ),
    )

    for operation in operations:
        with pytest.raises(
            ValueError,
            match="closed financial account",
        ):
            operation()


@pytest.mark.parametrize(
    "method_name",
    [
        "restrict",
        "suspend",
        "close",
    ],
)
def test_required_reason_rejects_empty_value(
    method_name: str,
) -> None:
    active = pending_account().activate(
        occurred_at=LATER
    )
    method = getattr(active, method_name)

    with pytest.raises(
        ValueError,
        match="lifecycle reason must not be empty",
    ):
        method(
            reason=" ",
            occurred_at=active.updated_at,
        )


def test_rename_returns_new_account() -> None:
    original = pending_account()
    occurred_at = LATER
    name = FinancialAccountName(
        "NovaPay Everyday Account",
        display_name="My Spending",
    )

    updated = original.rename(
        name,
        occurred_at=occurred_at,
    )

    assert updated.name == name
    assert original.name != updated.name
    assert_new_version(
        original,
        updated,
        occurred_at=occurred_at,
    )


def test_rename_rejects_no_op() -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must change name",
    ):
        account.rename(
            account.name,
            occurred_at=LATER,
        )


def test_change_terms_returns_new_account() -> None:
    original = pending_account()
    occurred_at = LATER

    updated = original.change_terms(
        {
            "overdraft_limit": "750",
            "maintenance_fee": "2.50",
        },
        occurred_at=occurred_at,
    )

    assert updated.terms.overdraft_limit == Decimal("750")
    assert updated.terms.maintenance_fee == Decimal("2.50")
    assert_new_version(
        original,
        updated,
        occurred_at=occurred_at,
    )


def test_change_terms_reapplies_account_type_invariant() -> None:
    savings = FinancialAccount.create(
        account_id="savings-001",
        customer_id="customer-001",
        tenant_id="tenant-001",
        account_type=FinancialAccountType.SAVINGS,
        purpose=FinancialAccountPurpose.SAVINGS,
        currency=aud_currency(),
        name=FinancialAccountName("NovaPay Savings"),
        wallet_id="wallet-001",
        terms=FinancialAccountTerms(
            interest_rate_percent="2"
        ),
        occurred_at=NOW,
    )

    with pytest.raises(
        ValueError,
        match="only current financial accounts",
    ):
        savings.change_terms(
            FinancialAccountTerms(
                interest_rate_percent="2",
                overdraft_limit="1",
            ),
            occurred_at=LATER,
        )


def test_change_terms_rejects_no_op() -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must change terms",
    ):
        account.change_terms(
            account.terms,
            occurred_at=LATER,
        )


def test_change_restrictions_returns_new_account() -> None:
    original = pending_account()

    updated = original.change_restrictions(
        {
            "cash_withdrawal_blocked": True,
            "allowed_channels": ["mobile"],
        },
        occurred_at=LATER,
    )

    assert (
        updated.restrictions.cash_withdrawal_blocked
        is True
    )
    assert updated.restrictions.allowed_channels == (
        "mobile",
    )
    assert_new_version(
        original,
        updated,
        occurred_at=LATER,
    )


def test_change_restrictions_rejects_no_op() -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must change restrictions",
    ):
        account.change_restrictions(
            account.restrictions,
            occurred_at=LATER,
        )


def test_update_metadata_returns_new_account() -> None:
    original = pending_account()

    updated = original.update_metadata(
        {
            "product_code": "CUR-002",
            "source": "branch",
        },
        occurred_at=LATER,
    )

    assert original.metadata.values == {
        "product_code": "CUR-001",
    }
    assert updated.metadata.values == {
        "product_code": "CUR-002",
        "source": "branch",
    }
    assert_new_version(
        original,
        updated,
        occurred_at=LATER,
    )


def test_update_metadata_rejects_sensitive_data() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        pending_account().update_metadata(
            {"access_token": "secret"},
            occurred_at=LATER,
        )


def test_update_metadata_rejects_no_op() -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        account.update_metadata(
            account.metadata,
            occurred_at=LATER,
        )


def test_link_wallet_returns_new_account() -> None:
    original = pending_account()

    updated = original.link_wallet(
        "wallet-002",
        occurred_at=LATER,
    )

    assert original.wallet_id == WalletId("wallet-001")
    assert updated.wallet_id == WalletId("wallet-002")
    assert_new_version(
        original,
        updated,
        occurred_at=LATER,
    )


def test_link_wallet_rejects_no_op() -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must change wallet id",
    ):
        account.link_wallet(
            account.wallet_id,
            occurred_at=LATER,
        )


def test_link_ledger_account_returns_new_account() -> None:
    original = pending_account()

    updated = original.link_ledger_account(
        "ledger-account-001",
        occurred_at=LATER,
    )

    assert original.ledger_account_id is None
    assert updated.ledger_account_id == LedgerAccountId(
        "ledger-account-001"
    )
    assert_new_version(
        original,
        updated,
        occurred_at=LATER,
    )


def test_link_ledger_account_rejects_no_op() -> None:
    account = pending_account().link_ledger_account(
        "ledger-account-001",
        occurred_at=LATER,
    )

    with pytest.raises(
        ValueError,
        match="must change ledger account id",
    ):
        account.link_ledger_account(
            account.ledger_account_id,
            occurred_at=account.updated_at,
        )


@pytest.mark.parametrize(
    "operation",
    [
        lambda account: account.rename(
            FinancialAccountName("Changed"),
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda account: account.change_terms(
            FinancialAccountTerms(
                overdraft_limit="100"
            ),
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda account: account.change_restrictions(
            FinancialAccountRestrictions(
                debit_blocked=True
            ),
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda account: account.update_metadata(
            {"source": "branch"},
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda account: account.link_wallet(
            "wallet-002",
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda account: account.link_ledger_account(
            "ledger-account-001",
            occurred_at=NOW - timedelta(seconds=1),
        ),
    ],
)
def test_updates_reject_earlier_timestamp(
    operation: object,
) -> None:
    account = pending_account()

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        operation(account)  # type: ignore[operator]


def test_equal_timestamp_is_allowed() -> None:
    account = pending_account()

    updated = account.rename(
        FinancialAccountName(
            "NovaPay Everyday Account",
            display_name="Everyday",
        ),
        occurred_at=account.updated_at,
    )

    assert updated.updated_at == account.updated_at
    assert updated.version == account.version + 1


def test_multiple_changes_increment_once_each() -> None:
    original = pending_account()

    active = original.activate(
        occurred_at=LATER
    )
    renamed = active.rename(
        FinancialAccountName(
            "NovaPay Everyday Account",
            display_name="My Account",
        ),
        occurred_at=LATER,
    )
    updated = renamed.update_metadata(
        {"product_code": "CUR-002"},
        occurred_at=LATER,
    )

    assert original.version == 1
    assert active.version == 2
    assert renamed.version == 3
    assert updated.version == 4


def test_original_account_remains_unchanged() -> None:
    original = pending_account()

    updated = original.activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    assert original.status is FinancialAccountStatus.PENDING
    assert original.version == 1
    assert original.updated_at == NOW
    assert original.metadata.values == {
        "product_code": "CUR-001",
    }

    assert updated.status is FinancialAccountStatus.ACTIVE
    assert updated.version == 2


def test_serialization_reflects_lifecycle_change() -> None:
    account = pending_account().activate(
        reason="verification complete",
        occurred_at=LATER,
    )

    payload = account.canonical_dict()

    assert payload["status"] == "active"
    assert payload["currency"] == "AUD"
    assert payload["version"] == 2
    assert payload["updated_at"] == LATER.isoformat()
    assert payload["metadata"]["lifecycle_action"] == (
        "activate"
    )


def test_lifecycle_methods_are_available() -> None:
    methods = (
        "activate",
        "restrict",
        "suspend",
        "mark_dormant",
        "reactivate",
        "close",
        "rename",
        "change_terms",
        "change_restrictions",
        "update_metadata",
        "link_wallet",
        "link_ledger_account",
    )

    for method in methods:
        assert callable(getattr(FinancialAccount, method))
