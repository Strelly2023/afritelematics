from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum

import pytest

from afritech.novapay.domain.financial_account import (
    FinancialAccountId,
    FinancialAccountPurpose,
    FinancialAccountStatus,
    FinancialAccountType,
)


def test_financial_account_id_trims_whitespace() -> None:
    account_id = FinancialAccountId(
        "  financial-account-001  "
    )

    assert account_id.value == "financial-account-001"


def test_financial_account_id_of_trims_whitespace() -> None:
    account_id = FinancialAccountId.of(
        "  financial-account-002  "
    )

    assert account_id == FinancialAccountId(
        "financial-account-002"
    )


def test_financial_account_id_of_returns_existing_instance() -> None:
    account_id = FinancialAccountId(
        "financial-account-003"
    )

    assert FinancialAccountId.of(account_id) is account_id


@pytest.mark.parametrize(
    "value",
    [
        "financial-account-001",
        "financial_account_001",
        "financial.account.001",
        "tenant:financial-account-001",
        "financial-account/001",
        "financial-account@platform",
    ],
)
def test_financial_account_id_accepts_supported_characters(
    value: str,
) -> None:
    assert FinancialAccountId(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_financial_account_id_rejects_empty_value(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="financial account id must not be empty",
    ):
        FinancialAccountId(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
        ["financial-account-001"],
        {"value": "financial-account-001"},
    ],
)
def test_financial_account_id_rejects_non_string_value(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="financial account id must be a string",
    ):
        FinancialAccountId.of(value)


@pytest.mark.parametrize(
    "value",
    [
        "financial account 001",
        "financial#account",
        "financial?account",
        "financial+account",
        "-financial-account",
    ],
)
def test_financial_account_id_rejects_unsupported_characters(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="contains unsupported characters",
    ):
        FinancialAccountId(value)


def test_financial_account_id_rejects_long_value() -> None:
    with pytest.raises(
        ValueError,
        match="contains unsupported characters",
    ):
        FinancialAccountId("a" * 129)


def test_financial_account_id_string_conversion() -> None:
    account_id = FinancialAccountId(
        "financial-account-001"
    )

    assert str(account_id) == "financial-account-001"


def test_financial_account_id_canonical_scalar() -> None:
    account_id = FinancialAccountId(
        "financial-account-001"
    )

    assert account_id.canonical() == (
        "financial-account-001"
    )


def test_financial_account_id_canonical_dict() -> None:
    account_id = FinancialAccountId(
        "financial-account-001"
    )

    assert account_id.canonical_dict() == {
        "value": "financial-account-001",
    }


def test_financial_account_id_value_equality_and_hashing() -> None:
    first = FinancialAccountId(
        "financial-account-001"
    )
    second = FinancialAccountId(
        "financial-account-001"
    )

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {
        FinancialAccountId(
            "financial-account-001"
        )
    }


def test_financial_account_id_supports_ordering() -> None:
    first = FinancialAccountId(
        "financial-account-001"
    )
    second = FinancialAccountId(
        "financial-account-002"
    )

    assert first < second


def test_financial_account_id_is_immutable() -> None:
    account_id = FinancialAccountId(
        "financial-account-001"
    )

    with pytest.raises(FrozenInstanceError):
        account_id.value = (  # type: ignore[misc]
            "financial-account-002"
        )


def test_financial_account_id_uses_slots() -> None:
    account_id = FinancialAccountId(
        "financial-account-001"
    )

    assert not hasattr(account_id, "__dict__")


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            FinancialAccountType.CURRENT,
            "current",
        ),
        (
            FinancialAccountType.SAVINGS,
            "savings",
        ),
        (
            FinancialAccountType.MERCHANT,
            "merchant",
        ),
        (
            FinancialAccountType.AGENT_FLOAT,
            "agent_float",
        ),
        (
            FinancialAccountType.SETTLEMENT,
            "settlement",
        ),
        (
            FinancialAccountType.TREASURY,
            "treasury",
        ),
        (
            FinancialAccountType.ESCROW,
            "escrow",
        ),
        (
            FinancialAccountType.PAYROLL,
            "payroll",
        ),
        (
            FinancialAccountType.BENEFIT,
            "benefit",
        ),
        (
            FinancialAccountType.LOAN,
            "loan",
        ),
        (
            FinancialAccountType.INVESTMENT,
            "investment",
        ),
        (
            FinancialAccountType.CLEARING,
            "clearing",
        ),
    ],
)
def test_financial_account_type_stable_values(
    member: FinancialAccountType,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "current",
            FinancialAccountType.CURRENT,
        ),
        (
            " CURRENT ",
            FinancialAccountType.CURRENT,
        ),
        (
            "Savings",
            FinancialAccountType.SAVINGS,
        ),
        (
            "MERCHANT",
            FinancialAccountType.MERCHANT,
        ),
        (
            " agent_float ",
            FinancialAccountType.AGENT_FLOAT,
        ),
        (
            "Settlement",
            FinancialAccountType.SETTLEMENT,
        ),
        (
            "TREASURY",
            FinancialAccountType.TREASURY,
        ),
        (
            "escrow",
            FinancialAccountType.ESCROW,
        ),
        (
            "Payroll",
            FinancialAccountType.PAYROLL,
        ),
        (
            "BENEFIT",
            FinancialAccountType.BENEFIT,
        ),
        (
            "loan",
            FinancialAccountType.LOAN,
        ),
        (
            "Investment",
            FinancialAccountType.INVESTMENT,
        ),
        (
            "CLEARING",
            FinancialAccountType.CLEARING,
        ),
    ],
)
def test_financial_account_type_parse_normalizes(
    raw: str,
    expected: FinancialAccountType,
) -> None:
    assert FinancialAccountType.parse(raw) is expected


def test_financial_account_type_parse_returns_existing() -> None:
    assert FinancialAccountType.parse(
        FinancialAccountType.SAVINGS
    ) is FinancialAccountType.SAVINGS


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "checking",
        "deposit",
        "wallet",
        "ledger",
        "unknown",
    ],
)
def test_financial_account_type_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        FinancialAccountType.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_financial_account_type_rejects_non_strings(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="financial account type must be a string",
    ):
        FinancialAccountType.parse(value)


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            FinancialAccountStatus.PENDING,
            "pending",
        ),
        (
            FinancialAccountStatus.ACTIVE,
            "active",
        ),
        (
            FinancialAccountStatus.RESTRICTED,
            "restricted",
        ),
        (
            FinancialAccountStatus.SUSPENDED,
            "suspended",
        ),
        (
            FinancialAccountStatus.DORMANT,
            "dormant",
        ),
        (
            FinancialAccountStatus.CLOSED,
            "closed",
        ),
    ],
)
def test_financial_account_status_stable_values(
    member: FinancialAccountStatus,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "pending",
            FinancialAccountStatus.PENDING,
        ),
        (
            " PENDING ",
            FinancialAccountStatus.PENDING,
        ),
        (
            "Active",
            FinancialAccountStatus.ACTIVE,
        ),
        (
            "RESTRICTED",
            FinancialAccountStatus.RESTRICTED,
        ),
        (
            " suspended ",
            FinancialAccountStatus.SUSPENDED,
        ),
        (
            "Dormant",
            FinancialAccountStatus.DORMANT,
        ),
        (
            "CLOSED",
            FinancialAccountStatus.CLOSED,
        ),
    ],
)
def test_financial_account_status_parse_normalizes(
    raw: str,
    expected: FinancialAccountStatus,
) -> None:
    assert FinancialAccountStatus.parse(raw) is expected


def test_financial_account_status_parse_returns_existing() -> None:
    assert FinancialAccountStatus.parse(
        FinancialAccountStatus.ACTIVE
    ) is FinancialAccountStatus.ACTIVE


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "frozen",
        "blocked",
        "deleted",
        "unknown",
    ],
)
def test_financial_account_status_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        FinancialAccountStatus.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_financial_account_status_rejects_non_strings(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="financial account status must be a string",
    ):
        FinancialAccountStatus.parse(value)


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            FinancialAccountPurpose.EVERYDAY_PAYMENTS,
            "everyday_payments",
        ),
        (
            FinancialAccountPurpose.SAVINGS,
            "savings",
        ),
        (
            FinancialAccountPurpose.MERCHANT_COLLECTIONS,
            "merchant_collections",
        ),
        (
            FinancialAccountPurpose.AGENT_LIQUIDITY,
            "agent_liquidity",
        ),
        (
            FinancialAccountPurpose.SETTLEMENT,
            "settlement",
        ),
        (
            FinancialAccountPurpose.TREASURY,
            "treasury",
        ),
        (
            FinancialAccountPurpose.ESCROW,
            "escrow",
        ),
        (
            FinancialAccountPurpose.PAYROLL,
            "payroll",
        ),
        (
            FinancialAccountPurpose.BENEFIT_DISBURSEMENT,
            "benefit_disbursement",
        ),
        (
            FinancialAccountPurpose.CREDIT,
            "credit",
        ),
        (
            FinancialAccountPurpose.INVESTMENT,
            "investment",
        ),
        (
            FinancialAccountPurpose.CLEARING,
            "clearing",
        ),
    ],
)
def test_financial_account_purpose_stable_values(
    member: FinancialAccountPurpose,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "everyday_payments",
            FinancialAccountPurpose.EVERYDAY_PAYMENTS,
        ),
        (
            " EVERYDAY_PAYMENTS ",
            FinancialAccountPurpose.EVERYDAY_PAYMENTS,
        ),
        (
            "Savings",
            FinancialAccountPurpose.SAVINGS,
        ),
        (
            "MERCHANT_COLLECTIONS",
            FinancialAccountPurpose.MERCHANT_COLLECTIONS,
        ),
        (
            " agent_liquidity ",
            FinancialAccountPurpose.AGENT_LIQUIDITY,
        ),
        (
            "Settlement",
            FinancialAccountPurpose.SETTLEMENT,
        ),
        (
            "TREASURY",
            FinancialAccountPurpose.TREASURY,
        ),
        (
            "escrow",
            FinancialAccountPurpose.ESCROW,
        ),
        (
            "Payroll",
            FinancialAccountPurpose.PAYROLL,
        ),
        (
            "BENEFIT_DISBURSEMENT",
            FinancialAccountPurpose.BENEFIT_DISBURSEMENT,
        ),
        (
            "credit",
            FinancialAccountPurpose.CREDIT,
        ),
        (
            "Investment",
            FinancialAccountPurpose.INVESTMENT,
        ),
        (
            "CLEARING",
            FinancialAccountPurpose.CLEARING,
        ),
    ],
)
def test_financial_account_purpose_parse_normalizes(
    raw: str,
    expected: FinancialAccountPurpose,
) -> None:
    assert FinancialAccountPurpose.parse(raw) is expected


def test_financial_account_purpose_parse_returns_existing() -> None:
    assert FinancialAccountPurpose.parse(
        FinancialAccountPurpose.SAVINGS
    ) is FinancialAccountPurpose.SAVINGS


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "general",
        "wallet",
        "ledger",
        "unknown",
    ],
)
def test_financial_account_purpose_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        FinancialAccountPurpose.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_financial_account_purpose_rejects_non_strings(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="financial account purpose must be a string",
    ):
        FinancialAccountPurpose.parse(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        FinancialAccountType,
        FinancialAccountStatus,
        FinancialAccountPurpose,
    ],
)
def test_financial_account_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


def test_financial_account_module_public_contract() -> None:
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
