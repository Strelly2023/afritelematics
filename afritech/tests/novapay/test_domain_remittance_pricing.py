from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.remittance import (
    RemittanceAmountBreakdown,
    RemittanceCharge,
    RemittanceFee,
    RemittanceFeeType,
    RemittancePricingMetadata,
)


def currency(code: str) -> Currency:
    parse = getattr(Currency, "parse", None)

    if callable(parse):
        try:
            result = parse(code)
        except (TypeError, ValueError):
            pass
        else:
            if isinstance(result, Currency):
                return result

    for attempt in (
        lambda: Currency(code),
        lambda: Currency(code=code),
    ):
        try:
            result = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Currency):
            return result

    raise AssertionError(
        f"unable to construct Currency for {code}"
    )


def money(amount: str, code: str) -> Money:
    amount_value = Decimal(amount)
    currency_value = currency(code)
    factory = getattr(Money, "of", None)

    attempts = []

    if callable(factory):
        attempts.extend(
            (
                lambda: factory(
                    amount_value,
                    currency_value,
                ),
                lambda: factory(
                    amount=amount_value,
                    currency=currency_value,
                ),
            )
        )

    attempts.extend(
        (
            lambda: Money(
                amount=amount_value,
                currency=currency_value,
            ),
            lambda: Money(
                amount_value,
                currency_value,
            ),
        )
    )

    for attempt in attempts:
        try:
            result = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Money):
            return result

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def fee(
    *,
    fee_type: object = "service",
    amount: Money | None = None,
    description: object = "NovaPay service fee",
    refundable: bool = False,
) -> RemittanceFee:
    return RemittanceFee.create(
        fee_type=fee_type,
        amount=(
            amount
            if amount is not None
            else money("2.50", "AUD")
        ),
        description=description,
        refundable=refundable,
    )


def charge(
    *,
    charge_id: object = "charge-001",
    charge_type: object = "regulatory levy",
    amount: Money | None = None,
    description: object = "Regulatory levy",
) -> RemittanceCharge:
    return RemittanceCharge.create(
        charge_id=charge_id,
        charge_type=charge_type,
        amount=(
            amount
            if amount is not None
            else money("0.50", "AUD")
        ),
        description=description,
    )


def breakdown(
    *,
    principal_amount: Money | None = None,
    fees: object = None,
    charges: object = None,
    fx_cost: Money | None = None,
    total_debit_amount: Money | None = None,
    destination_amount: Money | None = None,
    metadata: object = None,
) -> RemittanceAmountBreakdown:
    fee_values = (
        [fee()]
        if fees is None
        else fees
    )

    charge_values = (
        [charge()]
        if charges is None
        else charges
    )

    return RemittanceAmountBreakdown.create(
        principal_amount=(
            principal_amount
            if principal_amount is not None
            else money("100.00", "AUD")
        ),
        fees=fee_values,
        charges=charge_values,
        fx_cost=(
            fx_cost
            if fx_cost is not None
            else money("1.00", "AUD")
        ),
        total_debit_amount=(
            total_debit_amount
            if total_debit_amount is not None
            else money("104.00", "AUD")
        ),
        destination_amount=(
            destination_amount
            if destination_amount is not None
            else money("185000.00", "BIF")
        ),
        metadata=(
            {
                "pricing_version": "v1",
                "quote_reference": "quote-001",
            }
            if metadata is None
            else metadata
        ),
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("service", RemittanceFeeType.SERVICE),
        ("transfer", RemittanceFeeType.TRANSFER),
        ("provider", RemittanceFeeType.PROVIDER),
        ("network", RemittanceFeeType.NETWORK),
        ("compliance", RemittanceFeeType.COMPLIANCE),
        ("funding", RemittanceFeeType.FUNDING),
        ("delivery", RemittanceFeeType.DELIVERY),
        ("fx margin", RemittanceFeeType.FX_MARGIN),
        ("tax", RemittanceFeeType.TAX),
        ("other", RemittanceFeeType.OTHER),
    ],
)
def test_fee_type_parsing(
    raw: object,
    expected: RemittanceFeeType,
) -> None:
    assert RemittanceFeeType.parse(raw) is expected


def test_fee_type_preserves_instance() -> None:
    assert (
        RemittanceFeeType.parse(
            RemittanceFeeType.SERVICE
        )
        is RemittanceFeeType.SERVICE
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "unknown",
        None,
        1,
        object(),
    ],
)
def test_fee_type_rejects_invalid_values(
    value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        RemittanceFeeType.parse(value)


def test_fee_construction() -> None:
    amount = money("2.50", "AUD")

    value = fee(
        amount=amount,
        refundable=True,
    )

    assert value.fee_type is RemittanceFeeType.SERVICE
    assert value.amount is amount
    assert value.description == "NovaPay service fee"
    assert value.refundable is True
    assert value.currency_code == "AUD"


def test_fee_without_description() -> None:
    value = fee(description=None)

    assert value.description is None


def test_zero_fee_is_allowed() -> None:
    value = fee(
        amount=money("0.00", "AUD")
    )

    assert value.amount == money("0.00", "AUD")


def test_fee_is_immutable() -> None:
    value = fee()

    with pytest.raises(FrozenInstanceError):
        value.refundable = True  # type: ignore[misc]


def test_fee_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceFee)
    } == {
        "fee_type",
        "amount",
        "description",
        "refundable",
    }


def test_fee_canonical_dict() -> None:
    payload = fee(
        refundable=True,
    ).canonical_dict()

    assert list(payload) == [
        "fee_type",
        "amount",
        "description",
        "refundable",
    ]
    assert payload["fee_type"] == "service"
    assert "AUD" in str(payload["amount"])
    assert payload["description"] == "NovaPay service fee"
    assert payload["refundable"] is True


def test_fee_canonical_dict_is_fresh() -> None:
    value = fee()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["amount"] is not second["amount"]


def test_fee_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        fee(
            amount=money("-0.01", "AUD")
        )


def test_fee_rejects_non_money_amount() -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        fee(
            amount=object(),  # type: ignore[arg-type]
        )


def test_fee_rejects_non_boolean_refundable() -> None:
    with pytest.raises(
        TypeError,
        match="must be boolean",
    ):
        fee(
            refundable="yes",  # type: ignore[arg-type]
        )


def test_fee_rejects_empty_description() -> None:
    with pytest.raises(ValueError):
        fee(description="")


def test_charge_construction() -> None:
    amount = money("0.50", "AUD")

    value = charge(amount=amount)

    assert value.charge_id == "charge-001"
    assert value.charge_type == "regulatory_levy"
    assert value.amount is amount
    assert value.description == "Regulatory levy"
    assert value.currency_code == "AUD"


def test_charge_without_description() -> None:
    value = charge(description=None)

    assert value.description is None


def test_zero_charge_is_allowed() -> None:
    value = charge(
        amount=money("0.00", "AUD")
    )

    assert value.amount == money("0.00", "AUD")


def test_charge_is_immutable() -> None:
    value = charge()

    with pytest.raises(FrozenInstanceError):
        value.charge_id = "changed"  # type: ignore[misc]


def test_charge_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceCharge)
    } == {
        "charge_id",
        "charge_type",
        "amount",
        "description",
    }


def test_charge_canonical_dict() -> None:
    payload = charge().canonical_dict()

    assert list(payload) == [
        "charge_id",
        "charge_type",
        "amount",
        "description",
    ]
    assert payload["charge_id"] == "charge-001"
    assert payload["charge_type"] == "regulatory_levy"
    assert "AUD" in str(payload["amount"])
    assert payload["description"] == "Regulatory levy"


def test_charge_canonical_dict_is_fresh() -> None:
    value = charge()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["amount"] is not second["amount"]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("charge_id", ""),
        ("charge_type", ""),
        ("description", ""),
    ],
)
def test_charge_rejects_empty_text(
    field_name: str,
    value: str,
) -> None:
    kwargs: dict[str, object] = {
        "charge_id": "charge-001",
        "charge_type": "levy",
        "amount": money("1.00", "AUD"),
        "description": "description",
        field_name: value,
    }

    with pytest.raises(ValueError):
        RemittanceCharge.create(**kwargs)


def test_charge_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        charge(
            amount=money("-0.01", "AUD")
        )


def test_charge_rejects_non_money_amount() -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        charge(
            amount=object(),  # type: ignore[arg-type]
        )


def test_pricing_metadata_defaults_empty() -> None:
    value = RemittancePricingMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_pricing_metadata_preserves_instance() -> None:
    value = RemittancePricingMetadata.of(
        {"pricing_version": "v1"}
    )

    assert RemittancePricingMetadata.of(value) is value


def test_pricing_metadata_normalization() -> None:
    value = RemittancePricingMetadata.of(
        {
            "Pricing Version": "v1",
            "Quote Reference": "quote-001",
            "Tags": ["consumer", "international"],
        }
    )

    assert value.values == {
        "pricing_version": "v1",
        "quote_reference": "quote-001",
        "tags": (
            "consumer",
            "international",
        ),
    }


def test_pricing_metadata_is_immutable() -> None:
    value = RemittancePricingMetadata.of(
        {"pricing_version": "v1"}
    )

    with pytest.raises(FrozenInstanceError):
        value.values = {}  # type: ignore[misc]

    with pytest.raises(TypeError):
        value.values["pricing_version"] = "v2"  # type: ignore[index]


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "access_token",
        "api_key",
        "password",
        "pin",
        "private_key",
        "secret",
        "token",
    ],
)
def test_pricing_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        RemittancePricingMetadata.of(
            {key: "sensitive"}
        )


def test_amount_breakdown_construction() -> None:
    service_fee = fee()
    regulatory_charge = charge()

    value = breakdown(
        fees=[service_fee],
        charges=[regulatory_charge],
    )

    assert value.fees == (service_fee,)
    assert value.charges == (regulatory_charge,)
    assert value.source_currency_code == "AUD"
    assert value.destination_currency_code == "BIF"
    assert value.fee_total == Decimal("2.50")
    assert value.charge_total == Decimal("0.50")
    assert value.fx_cost_total == Decimal("1.00")
    assert value.is_cross_currency is True


def test_amount_breakdown_tuple_normalization() -> None:
    value = breakdown(
        fees=[fee()],
        charges=[charge()],
    )

    assert isinstance(value.fees, tuple)
    assert isinstance(value.charges, tuple)


def test_amount_breakdown_empty_fees_and_charges() -> None:
    value = breakdown(
        fees=[],
        charges=[],
        fx_cost=money("0.00", "AUD"),
        total_debit_amount=money("100.00", "AUD"),
    )

    assert value.fees == ()
    assert value.charges == ()
    assert value.fee_total == Decimal("0")
    assert value.charge_total == Decimal("0")
    assert value.fx_cost_total == Decimal("0.00")


def test_amount_breakdown_same_currency() -> None:
    value = breakdown(
        destination_amount=money("100.00", "AUD"),
    )

    assert value.is_cross_currency is False


def test_amount_breakdown_preserves_money_instances() -> None:
    principal = money("100.00", "AUD")
    fx_cost = money("1.00", "AUD")
    total = money("104.00", "AUD")
    destination = money("185000.00", "BIF")

    value = breakdown(
        principal_amount=principal,
        fx_cost=fx_cost,
        total_debit_amount=total,
        destination_amount=destination,
    )

    assert value.principal_amount is principal
    assert value.fx_cost is fx_cost
    assert value.total_debit_amount is total
    assert value.destination_amount is destination


def test_amount_breakdown_metadata_preservation() -> None:
    metadata = RemittancePricingMetadata.of(
        {"pricing_version": "v1"}
    )

    value = breakdown(metadata=metadata)

    assert value.metadata is metadata


def test_amount_breakdown_is_immutable() -> None:
    value = breakdown()

    with pytest.raises(FrozenInstanceError):
        value.fees = ()  # type: ignore[misc]


def test_amount_breakdown_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceAmountBreakdown)
    } == {
        "principal_amount",
        "fees",
        "charges",
        "fx_cost",
        "total_debit_amount",
        "destination_amount",
        "metadata",
    }


def test_amount_breakdown_canonical_dict() -> None:
    payload = breakdown().canonical_dict()

    assert list(payload) == [
        "principal_amount",
        "fees",
        "charges",
        "fx_cost",
        "total_debit_amount",
        "destination_amount",
        "metadata",
    ]

    assert "AUD" in str(payload["principal_amount"])
    assert len(payload["fees"]) == 1
    assert len(payload["charges"]) == 1
    assert payload["fees"][0]["fee_type"] == "service"
    assert payload["charges"][0]["charge_type"] == (
        "regulatory_levy"
    )
    assert "AUD" in str(payload["fx_cost"])
    assert "AUD" in str(payload["total_debit_amount"])
    assert "BIF" in str(payload["destination_amount"])
    assert payload["metadata"] == {
        "pricing_version": "v1",
        "quote_reference": "quote-001",
    }


def test_amount_breakdown_canonical_dict_is_fresh() -> None:
    value = breakdown()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["principal_amount"]
        is not second["principal_amount"]
    )
    assert first["fees"] is not second["fees"]
    assert first["fees"][0] is not second["fees"][0]
    assert first["charges"] is not second["charges"]
    assert first["charges"][0] is not second["charges"][0]
    assert first["fx_cost"] is not second["fx_cost"]
    assert (
        first["total_debit_amount"]
        is not second["total_debit_amount"]
    )
    assert (
        first["destination_amount"]
        is not second["destination_amount"]
    )
    assert first["metadata"] is not second["metadata"]


def test_amount_breakdown_rejects_non_positive_principal() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        breakdown(
            principal_amount=money("0.00", "AUD")
        )


def test_amount_breakdown_rejects_negative_principal() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        breakdown(
            principal_amount=money("-1.00", "AUD")
        )


def test_amount_breakdown_rejects_non_fee_items() -> None:
    with pytest.raises(
        TypeError,
        match="RemittanceFee",
    ):
        breakdown(
            fees=[object()],
        )


def test_amount_breakdown_rejects_non_charge_items() -> None:
    with pytest.raises(
        TypeError,
        match="RemittanceCharge",
    ):
        breakdown(
            charges=[object()],
        )


def test_amount_breakdown_rejects_fee_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="fee currency",
    ):
        breakdown(
            fees=[
                fee(
                    amount=money("2.50", "USD")
                )
            ]
        )


def test_amount_breakdown_rejects_charge_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="charge currency",
    ):
        breakdown(
            charges=[
                charge(
                    amount=money("0.50", "USD")
                )
            ]
        )


def test_amount_breakdown_rejects_fx_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="FX cost currency",
    ):
        breakdown(
            fx_cost=money("1.00", "USD")
        )


def test_amount_breakdown_rejects_negative_fx_cost() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        breakdown(
            fx_cost=money("-1.00", "AUD"),
            total_debit_amount=money("102.00", "AUD"),
        )


def test_amount_breakdown_rejects_total_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="total debit currency",
    ):
        breakdown(
            total_debit_amount=money("104.00", "USD")
        )


@pytest.mark.parametrize(
    "total",
    [
        "103.99",
        "104.01",
        "1.00",
    ],
)
def test_amount_breakdown_rejects_incorrect_total(
    total: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must equal principal",
    ):
        breakdown(
            total_debit_amount=money(total, "AUD")
        )


@pytest.mark.parametrize(
    "amount",
    [
        "0.00",
        "-1.00",
    ],
)
def test_amount_breakdown_rejects_non_positive_destination(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        breakdown(
            destination_amount=money(amount, "BIF")
        )


def test_amount_breakdown_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        breakdown(
            metadata={
                "authorization": "secret",
            }
        )


def test_pricing_domain_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    import afritech.novapay.domain.remittance as remittance

    for symbol in (
        "RemittanceFeeType",
        "RemittanceFee",
        "RemittanceCharge",
        "RemittancePricingMetadata",
        "RemittanceAmountBreakdown",
    ):
        module_value = getattr(remittance, symbol)

        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_pricing_domain_has_no_runtime_authority() -> None:
    value_types = (
        RemittanceFee,
        RemittanceCharge,
        RemittancePricingMetadata,
        RemittanceAmountBreakdown,
    )

    for value_type in value_types:
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "collect",
            "collect_fee",
            "authorize_funds",
            "reserve",
            "reserve_funds",
            "debit",
            "credit",
            "post",
            "post_entry",
            "settle",
            "execute",
            "submit",
            "submit_to_provider",
            "send",
            "route",
            "select_provider",
            "convert",
            "lock_rate",
            "save",
            "persist",
            "repository",
            "database",
        ):
            assert forbidden not in names


def test_pricing_fields_have_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(RemittanceAmountBreakdown)
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "provider_client",
        "settlement_engine",
        "fx_engine",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names
