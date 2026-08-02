from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.financial_account import (
    FinancialAccountMetadata,
    FinancialAccountName,
    FinancialAccountRestrictions,
    FinancialAccountTerms,
)


def test_financial_account_name_normalizes_product_name() -> None:
    name = FinancialAccountName(
        "  NovaPay   Everyday   Account "
    )

    assert name.product_name == "NovaPay Everyday Account"
    assert name.display_name is None


def test_financial_account_name_normalizes_display_name() -> None:
    name = FinancialAccountName(
        "NovaPay Everyday Account",
        display_name="  Everyday   Account ",
    )

    assert name.display_name == "Everyday Account"
    assert name.effective_display_name == "Everyday Account"


def test_financial_account_name_falls_back_to_product_name() -> None:
    name = FinancialAccountName(
        "NovaPay Savings Account"
    )

    assert name.effective_display_name == (
        "NovaPay Savings Account"
    )


def test_financial_account_name_of_returns_existing() -> None:
    name = FinancialAccountName(
        "NovaPay Savings Account"
    )

    assert FinancialAccountName.of(name) is name


def test_financial_account_name_of_rejects_display_for_existing() -> None:
    name = FinancialAccountName(
        "NovaPay Savings Account"
    )

    with pytest.raises(
        ValueError,
        match="display name must not be supplied",
    ):
        FinancialAccountName.of(
            name,
            display_name="Savings",
        )


@pytest.mark.parametrize(
    "value",
    ["", " ", "\t", "\n"],
)
def test_financial_account_name_rejects_empty_product_name(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="product name must not be empty",
    ):
        FinancialAccountName(value)


def test_financial_account_name_rejects_long_product_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 160 characters",
    ):
        FinancialAccountName("x" * 161)


def test_financial_account_name_rejects_long_display_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 120 characters",
    ):
        FinancialAccountName(
            "NovaPay Account",
            display_name="x" * 121,
        )


def test_financial_account_name_is_immutable() -> None:
    name = FinancialAccountName("NovaPay Account")

    with pytest.raises(FrozenInstanceError):
        name.product_name = "Changed"  # type: ignore[misc]


def test_financial_account_name_canonical_dict() -> None:
    name = FinancialAccountName(
        "NovaPay Savings Account",
        display_name="My Savings",
    )

    assert name.canonical_dict() == {
        "product_name": "NovaPay Savings Account",
        "display_name": "My Savings",
    }


def test_financial_account_terms_defaults() -> None:
    terms = FinancialAccountTerms()

    assert terms.minimum_balance == Decimal("0")
    assert terms.overdraft_limit == Decimal("0")
    assert terms.interest_rate_percent == Decimal("0")
    assert terms.maintenance_fee == Decimal("0")
    assert terms.notice_period_days is None


def test_financial_account_terms_normalize_numeric_values() -> None:
    terms = FinancialAccountTerms(
        minimum_balance="100.00",
        overdraft_limit=250,
        interest_rate_percent="4.5",
        maintenance_fee="2.99",
        notice_period_days=30,
    )

    assert terms.minimum_balance == Decimal("100.00")
    assert terms.overdraft_limit == Decimal("250")
    assert terms.interest_rate_percent == Decimal("4.5")
    assert terms.maintenance_fee == Decimal("2.99")
    assert terms.notice_period_days == 30


@pytest.mark.parametrize(
    "field_name",
    [
        "minimum_balance",
        "overdraft_limit",
        "interest_rate_percent",
        "maintenance_fee",
    ],
)
def test_financial_account_terms_reject_negative_values(
    field_name: str,
) -> None:
    values = {
        "minimum_balance": Decimal("0"),
        "overdraft_limit": Decimal("0"),
        "interest_rate_percent": Decimal("0"),
        "maintenance_fee": Decimal("0"),
    }
    values[field_name] = Decimal("-0.01")

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        FinancialAccountTerms(**values)


@pytest.mark.parametrize(
    "value",
    [
        "not-a-number",
        object(),
        True,
    ],
)
def test_financial_account_terms_reject_invalid_numeric_values(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        FinancialAccountTerms(
            minimum_balance=value,
        )


def test_financial_account_terms_reject_interest_over_100() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 100",
    ):
        FinancialAccountTerms(
            interest_rate_percent="100.01",
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_financial_account_terms_reject_invalid_notice_period(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        FinancialAccountTerms(
            notice_period_days=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        30.0,
        "30",
    ],
)
def test_financial_account_terms_reject_non_integer_notice_period(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        FinancialAccountTerms(
            notice_period_days=value,
        )


def test_financial_account_terms_canonical_dict() -> None:
    terms = FinancialAccountTerms(
        minimum_balance="100.00",
        overdraft_limit="250.00",
        interest_rate_percent="4.5",
        maintenance_fee="2.99",
        notice_period_days=30,
    )

    assert terms.canonical_dict() == {
        "minimum_balance": "100.00",
        "overdraft_limit": "250.00",
        "interest_rate_percent": "4.5",
        "maintenance_fee": "2.99",
        "notice_period_days": 30,
    }


def test_financial_account_restrictions_defaults() -> None:
    restrictions = FinancialAccountRestrictions()

    assert restrictions.debit_blocked is False
    assert restrictions.credit_blocked is False
    assert restrictions.cash_withdrawal_blocked is False
    assert restrictions.international_transfer_blocked is False
    assert restrictions.allowed_channels == ()
    assert restrictions.allowed_countries == ()
    assert restrictions.fully_blocked is False


def test_financial_account_restrictions_normalize_collections() -> None:
    restrictions = FinancialAccountRestrictions(
        allowed_channels=[
            " MOBILE ",
            "Agent",
            "WEB",
        ],
        allowed_countries=[
            "au",
            " bi ",
            "CD",
        ],
    )

    assert restrictions.allowed_channels == (
        "mobile",
        "agent",
        "web",
    )
    assert restrictions.allowed_countries == (
        "AU",
        "BI",
        "CD",
    )


def test_financial_account_restrictions_detect_fully_blocked() -> None:
    restrictions = FinancialAccountRestrictions(
        debit_blocked=True,
        credit_blocked=True,
    )

    assert restrictions.fully_blocked is True


@pytest.mark.parametrize(
    "field_name",
    [
        "debit_blocked",
        "credit_blocked",
        "cash_withdrawal_blocked",
        "international_transfer_blocked",
    ],
)
def test_financial_account_restrictions_require_boolean_flags(
    field_name: str,
) -> None:
    values = {
        "debit_blocked": False,
        "credit_blocked": False,
        "cash_withdrawal_blocked": False,
        "international_transfer_blocked": False,
    }
    values[field_name] = "false"

    with pytest.raises(
        TypeError,
        match="must be a boolean",
    ):
        FinancialAccountRestrictions(**values)


def test_financial_account_restrictions_reject_duplicate_channels() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        FinancialAccountRestrictions(
            allowed_channels=[
                "mobile",
                " MOBILE ",
            ]
        )


def test_financial_account_restrictions_reject_duplicate_countries() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        FinancialAccountRestrictions(
            allowed_countries=[
                "au",
                " AU ",
            ]
        )


@pytest.mark.parametrize(
    "country",
    [
        "A",
        "AUS",
        "12",
        "A1",
    ],
)
def test_financial_account_restrictions_reject_invalid_country(
    country: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="two-letter country codes",
    ):
        FinancialAccountRestrictions(
            allowed_countries=[country]
        )


def test_financial_account_restrictions_canonical_dict() -> None:
    restrictions = FinancialAccountRestrictions(
        debit_blocked=True,
        allowed_channels=["mobile"],
        allowed_countries=["AU"],
    )

    assert restrictions.canonical_dict() == {
        "debit_blocked": True,
        "credit_blocked": False,
        "cash_withdrawal_blocked": False,
        "international_transfer_blocked": False,
        "allowed_channels": ["mobile"],
        "allowed_countries": ["AU"],
    }


def test_financial_account_metadata_defaults_empty() -> None:
    metadata = FinancialAccountMetadata()

    assert dict(metadata.values) == {}
    assert isinstance(metadata.values, MappingProxyType)


def test_financial_account_metadata_normalizes_keys() -> None:
    metadata = FinancialAccountMetadata(
        {
            " product_code ": "SAV-001",
            "source": "mobile",
        }
    )

    assert metadata.values == {
        "product_code": "SAV-001",
        "source": "mobile",
    }


def test_financial_account_metadata_defensive_copy() -> None:
    source = {"product_code": "SAV-001"}
    metadata = FinancialAccountMetadata(source)

    source["product_code"] = "CHANGED"

    assert metadata.get("product_code") == "SAV-001"


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "access_token",
        "refresh_token",
        "api_key",
        "private_key",
        "pin",
        "cvv",
        "card_number",
        "biometric_template",
        "identity_document",
        "document_image",
        "credential_payload",
    ],
)
def test_financial_account_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        FinancialAccountMetadata(
            {key: "secret"}
        )


def test_financial_account_metadata_sensitive_check_case_insensitive() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        FinancialAccountMetadata(
            {"Access_Token": "secret"}
        )


def test_financial_account_metadata_with_value_revalidates() -> None:
    metadata = FinancialAccountMetadata(
        {"product_code": "SAV-001"}
    )

    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        metadata.with_value(
            "refresh_token",
            "secret",
        )


def test_financial_account_metadata_without_is_immutable() -> None:
    original = FinancialAccountMetadata(
        {
            "product_code": "SAV-001",
            "source": "mobile",
        }
    )

    updated = original.without("source")

    assert "source" in original.values
    assert "source" not in updated.values


def test_financial_account_metadata_canonical_dict_is_immutable() -> None:
    metadata = FinancialAccountMetadata(
        {"product_code": "SAV-001"}
    )

    payload = metadata.canonical_dict()

    assert isinstance(payload, MappingProxyType)

    with pytest.raises(TypeError):
        payload["product_code"] = "X"  # type: ignore[index]


@pytest.mark.parametrize(
    "value",
    [
        123,
        object(),
        ["product_code"],
    ],
)
def test_financial_account_metadata_rejects_non_mapping(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        FinancialAccountMetadata.of(value)


def test_financial_account_value_objects_are_slotted() -> None:
    values = (
        FinancialAccountName("NovaPay Account"),
        FinancialAccountTerms(),
        FinancialAccountRestrictions(),
        FinancialAccountMetadata(),
    )

    for value in values:
        assert not hasattr(value, "__dict__")


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
