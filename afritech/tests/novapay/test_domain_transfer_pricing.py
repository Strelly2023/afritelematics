from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.transfer import (
    TransferAmountBreakdown,
    TransferCharge,
    TransferFee,
    TransferFeeType,
    TransferPricingMetadata,
)


def currency(code: str) -> Currency:
    parse = getattr(Currency, "parse", None)

    if callable(parse):
        try:
            value = parse(code)
        except (TypeError, ValueError):
            pass
        else:
            if isinstance(value, Currency):
                return value

    for attempt in (
        lambda: Currency(code),
        lambda: Currency(code=code),
    ):
        try:
            value = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(value, Currency):
            return value

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
            value = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(value, Money):
            return value

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def service_fee(
    amount: str = "2.50",
    code: str = "AUD",
) -> TransferFee:
    return TransferFee.create(
        fee_type="service",
        amount=money(amount, code),
        description="NovaPay service fee",
        refundable=False,
        metadata={
            "source": "novapay",
        },
    )


def network_fee(
    amount: str = "1.25",
    code: str = "AUD",
) -> TransferFee:
    return TransferFee.create(
        fee_type="network",
        amount=money(amount, code),
    )


def partner_charge(
    amount: str = "0.75",
    code: str = "AUD",
) -> TransferCharge:
    return TransferCharge.create(
        charge_code="partner_delivery",
        amount=money(amount, code),
        description="Partner delivery charge",
        third_party=True,
        metadata={
            "partner": "delivery-network",
        },
    )


def breakdown(
    *,
    source_amount: Money | None = None,
    destination_amount: Money | None = None,
    fees: object = None,
    charges: object = None,
    fee_total: Money | None = None,
    charge_total: Money | None = None,
    total_debit_amount: Money | None = None,
    metadata: object = None,
) -> TransferAmountBreakdown:
    fee_values = (
        (service_fee(), network_fee())
        if fees is None
        else fees
    )
    charge_values = (
        (partner_charge(),)
        if charges is None
        else charges
    )

    return TransferAmountBreakdown.create(
        source_amount=(
            source_amount
            if source_amount is not None
            else money("100.00", "AUD")
        ),
        destination_amount=(
            destination_amount
            if destination_amount is not None
            else money("65.00", "USD")
        ),
        fees=fee_values,
        charges=charge_values,
        fee_total=(
            fee_total
            if fee_total is not None
            else money("3.75", "AUD")
        ),
        charge_total=(
            charge_total
            if charge_total is not None
            else money("0.75", "AUD")
        ),
        total_debit_amount=(
            total_debit_amount
            if total_debit_amount is not None
            else money("104.50", "AUD")
        ),
        metadata=(
            metadata
            if metadata is not None
            else {
                "pricing_version": "v1",
                "corridor": "AU-US",
            }
        ),
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("service", TransferFeeType.SERVICE),
        ("processing", TransferFeeType.PROCESSING),
        ("network", TransferFeeType.NETWORK),
        ("delivery", TransferFeeType.DELIVERY),
        ("compliance", TransferFeeType.COMPLIANCE),
        ("fx-margin", TransferFeeType.FX_MARGIN),
        ("agent", TransferFeeType.AGENT),
        ("partner", TransferFeeType.PARTNER),
        ("tax", TransferFeeType.TAX),
        ("other", TransferFeeType.OTHER),
    ],
)
def test_fee_type_parse(
    raw: str,
    expected: TransferFeeType,
) -> None:
    assert TransferFeeType.parse(raw) is expected


def test_fee_type_inventory() -> None:
    assert tuple(
        item.value
        for item in TransferFeeType
    ) == (
        "service",
        "processing",
        "network",
        "delivery",
        "compliance",
        "fx_margin",
        "agent",
        "partner",
        "tax",
        "other",
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "unknown",
        None,
        1,
    ],
)
def test_fee_type_rejects_invalid_value(
    value: object,
) -> None:
    expected = (
        TypeError
        if not isinstance(value, str)
        else ValueError
    )

    with pytest.raises(expected):
        TransferFeeType.parse(value)


def test_pricing_metadata_defaults_empty() -> None:
    value = TransferPricingMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_pricing_metadata_normalizes() -> None:
    value = TransferPricingMetadata.of(
        {
            "Pricing Version": "v1",
            "tags": [
                "consumer",
                "international",
            ],
        }
    )

    assert value.values["pricing_version"] == "v1"
    assert value.values["tags"] == (
        "consumer",
        "international",
    )


def test_pricing_metadata_preserves_instance() -> None:
    value = TransferPricingMetadata.of(
        {
            "source": "novapay",
        }
    )

    assert TransferPricingMetadata.of(value) is value


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "password",
        "access_token",
        "authorization",
        "private-key",
        "pin",
    ],
)
def test_pricing_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        TransferPricingMetadata.of(
            {
                key: "sensitive",
            }
        )


def test_transfer_fee_construction() -> None:
    value = service_fee()

    assert value.fee_type is TransferFeeType.SERVICE
    assert value.currency_code == "AUD"
    assert value.amount_decimal == Decimal("2.50")
    assert value.description == "NovaPay service fee"
    assert value.refundable is False
    assert value.metadata.values["source"] == "novapay"


def test_transfer_fee_normalizes_description() -> None:
    value = TransferFee.create(
        fee_type="network",
        amount=money("1.00", "AUD"),
        description=" Network fee ",
    )

    assert value.description == "Network fee"


def test_transfer_fee_preserves_money_instance() -> None:
    amount = money("2.50", "AUD")
    value = TransferFee.create(
        fee_type="service",
        amount=amount,
    )

    assert value.amount is amount


def test_transfer_fee_zero_is_allowed() -> None:
    value = TransferFee.create(
        fee_type="service",
        amount=money("0.00", "AUD"),
    )

    assert value.amount_decimal == Decimal("0.00")


def test_transfer_fee_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        TransferFee.create(
            fee_type="service",
            amount=money("-0.01", "AUD"),
        )


def test_transfer_fee_rejects_non_money() -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        TransferFee.create(
            fee_type="service",
            amount="2.50",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "value",
    [
        1,
        "true",
        None,
    ],
)
def test_transfer_fee_rejects_non_boolean_refundable(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a boolean",
    ):
        TransferFee(
            fee_type=TransferFeeType.SERVICE,
            amount=money("2.50", "AUD"),
            refundable=value,  # type: ignore[arg-type]
        )


def test_transfer_fee_is_immutable() -> None:
    value = service_fee()

    with pytest.raises(FrozenInstanceError):
        value.refundable = True  # type: ignore[misc]


def test_transfer_fee_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(TransferFee)
    } == {
        "fee_type",
        "amount",
        "description",
        "refundable",
        "metadata",
    }


def test_transfer_fee_canonical_dict() -> None:
    payload = service_fee().canonical_dict()

    assert list(payload) == [
        "fee_type",
        "amount",
        "description",
        "refundable",
        "metadata",
    ]
    assert payload["fee_type"] == "service"
    assert "AUD" in str(payload["amount"])
    assert payload["description"] == (
        "NovaPay service fee"
    )
    assert payload["refundable"] is False
    assert payload["metadata"] == {
        "source": "novapay",
    }


def test_transfer_charge_construction() -> None:
    value = partner_charge()

    assert value.charge_code == "partner_delivery"
    assert value.currency_code == "AUD"
    assert value.amount_decimal == Decimal("0.75")
    assert value.third_party is True
    assert value.metadata.values["partner"] == (
        "delivery-network"
    )


def test_transfer_charge_normalizes_code() -> None:
    value = TransferCharge.create(
        charge_code=" Partner Delivery ",
        amount=money("0.75", "AUD"),
    )

    assert value.charge_code == "partner_delivery"


def test_transfer_charge_preserves_money_instance() -> None:
    amount = money("0.75", "AUD")
    value = TransferCharge.create(
        charge_code="partner",
        amount=amount,
    )

    assert value.amount is amount


def test_transfer_charge_zero_is_allowed() -> None:
    value = TransferCharge.create(
        charge_code="partner",
        amount=money("0.00", "AUD"),
    )

    assert value.amount_decimal == Decimal("0.00")


def test_transfer_charge_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        TransferCharge.create(
            charge_code="partner",
            amount=money("-0.01", "AUD"),
        )


def test_transfer_charge_rejects_blank_code() -> None:
    with pytest.raises(
        ValueError,
        match="charge code is required",
    ):
        TransferCharge.create(
            charge_code=" ",
            amount=money("0.75", "AUD"),
        )


@pytest.mark.parametrize(
    "value",
    [
        1,
        "true",
        None,
    ],
)
def test_transfer_charge_rejects_non_boolean_third_party(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a boolean",
    ):
        TransferCharge(
            charge_code="partner",
            amount=money("0.75", "AUD"),
            third_party=value,  # type: ignore[arg-type]
        )


def test_transfer_charge_is_immutable() -> None:
    value = partner_charge()

    with pytest.raises(FrozenInstanceError):
        value.third_party = False  # type: ignore[misc]


def test_transfer_charge_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(TransferCharge)
    } == {
        "charge_code",
        "amount",
        "description",
        "third_party",
        "metadata",
    }


def test_transfer_charge_canonical_dict() -> None:
    payload = partner_charge().canonical_dict()

    assert list(payload) == [
        "charge_code",
        "amount",
        "description",
        "third_party",
        "metadata",
    ]
    assert payload["charge_code"] == (
        "partner_delivery"
    )
    assert "AUD" in str(payload["amount"])
    assert payload["third_party"] is True


def test_amount_breakdown_construction() -> None:
    value = breakdown()

    assert len(value.fees) == 2
    assert len(value.charges) == 1
    assert value.source_currency_code == "AUD"
    assert value.destination_currency_code == "USD"
    assert value.is_cross_currency is True


def test_amount_breakdown_preserves_money_instances() -> None:
    source = money("100.00", "AUD")
    destination = money("65.00", "USD")
    fee_total = money("3.75", "AUD")
    charge_total = money("0.75", "AUD")
    debit_total = money("104.50", "AUD")

    value = breakdown(
        source_amount=source,
        destination_amount=destination,
        fee_total=fee_total,
        charge_total=charge_total,
        total_debit_amount=debit_total,
    )

    assert value.source_amount is source
    assert value.destination_amount is destination
    assert value.fee_total is fee_total
    assert value.charge_total is charge_total
    assert value.total_debit_amount is debit_total


def test_amount_breakdown_converts_lists_to_tuples() -> None:
    fees = [
        service_fee(),
        network_fee(),
    ]
    charges = [
        partner_charge(),
    ]

    value = breakdown(
        fees=fees,
        charges=charges,
    )

    assert isinstance(value.fees, tuple)
    assert isinstance(value.charges, tuple)


def test_amount_breakdown_same_currency() -> None:
    value = breakdown(
        destination_amount=money(
            "100.00",
            "AUD",
        )
    )

    assert value.is_cross_currency is False


def test_empty_fee_and_charge_breakdown() -> None:
    value = breakdown(
        fees=(),
        charges=(),
        fee_total=money("0.00", "AUD"),
        charge_total=money("0.00", "AUD"),
        total_debit_amount=money(
            "100.00",
            "AUD",
        ),
    )

    assert value.fees == ()
    assert value.charges == ()


def test_fee_total_validation() -> None:
    with pytest.raises(
        ValueError,
        match="fee total does not match",
    ):
        breakdown(
            fee_total=money("4.00", "AUD"),
        )


def test_charge_total_validation() -> None:
    with pytest.raises(
        ValueError,
        match="charge total does not match",
    ):
        breakdown(
            charge_total=money("1.00", "AUD"),
        )


def test_total_debit_validation() -> None:
    with pytest.raises(
        ValueError,
        match="total debit amount does not match",
    ):
        breakdown(
            total_debit_amount=money(
                "105.00",
                "AUD",
            ),
        )


def test_fee_currency_must_match_source() -> None:
    with pytest.raises(
        ValueError,
        match="fee currency must match",
    ):
        breakdown(
            fees=(
                service_fee(
                    amount="2.50",
                    code="USD",
                ),
                network_fee(),
            ),
            fee_total=money("3.75", "AUD"),
        )


def test_charge_currency_must_match_source() -> None:
    with pytest.raises(
        ValueError,
        match="charge currency must match",
    ):
        breakdown(
            charges=(
                partner_charge(
                    amount="0.75",
                    code="USD",
                ),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        (
            "fee_total",
            lambda: money("3.75", "USD"),
        ),
        (
            "charge_total",
            lambda: money("0.75", "USD"),
        ),
        (
            "total_debit_amount",
            lambda: money("104.50", "USD"),
        ),
    ],
)
def test_declared_totals_must_match_source_currency(
    field_name: str,
    replacement: object,
) -> None:
    kwargs = {
        field_name: replacement(),  # type: ignore[operator]
    }

    with pytest.raises(
        ValueError,
        match="currency must match source amount currency",
    ):
        breakdown(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    [
        "source_amount",
        "destination_amount",
        "fee_total",
        "charge_total",
        "total_debit_amount",
    ],
)
def test_breakdown_rejects_negative_money_fields(
    field_name: str,
) -> None:
    code = (
        "USD"
        if field_name == "destination_amount"
        else "AUD"
    )

    kwargs = {
        field_name: money("-0.01", code),
    }

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        breakdown(**kwargs)


def test_breakdown_rejects_non_fee_item() -> None:
    with pytest.raises(
        TypeError,
        match="fees must contain TransferFee",
    ):
        breakdown(
            fees=(
                service_fee(),
                object(),
            ),
        )


def test_breakdown_rejects_non_charge_item() -> None:
    with pytest.raises(
        TypeError,
        match="charges must contain TransferCharge",
    ):
        breakdown(
            charges=(
                partner_charge(),
                object(),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("fees", 1),
        ("charges", 1),
    ],
)
def test_breakdown_rejects_non_iterable_collections(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        field_name: value,
    }

    with pytest.raises(
        TypeError,
        match="must be iterable",
    ):
        breakdown(**kwargs)


def test_amount_breakdown_metadata_normalization() -> None:
    value = breakdown(
        metadata={
            "Pricing Version": "v2",
        }
    )

    assert value.metadata.values[
        "pricing_version"
    ] == "v2"


def test_amount_breakdown_is_immutable() -> None:
    value = breakdown()

    with pytest.raises(FrozenInstanceError):
        value.fees = ()  # type: ignore[misc]


def test_amount_breakdown_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(
            TransferAmountBreakdown
        )
    } == {
        "source_amount",
        "destination_amount",
        "fees",
        "charges",
        "fee_total",
        "charge_total",
        "total_debit_amount",
        "metadata",
    }


def test_amount_breakdown_canonical_dict() -> None:
    payload = breakdown().canonical_dict()

    assert list(payload) == [
        "source_amount",
        "destination_amount",
        "fees",
        "charges",
        "fee_total",
        "charge_total",
        "total_debit_amount",
        "metadata",
    ]
    assert len(payload["fees"]) == 2
    assert len(payload["charges"]) == 1
    assert payload["fees"][0][
        "fee_type"
    ] == "service"
    assert payload["charges"][0][
        "charge_code"
    ] == "partner_delivery"
    assert "104.50" in str(
        payload["total_debit_amount"]
    )


def test_amount_breakdown_canonical_dict_is_fresh() -> None:
    value = breakdown()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["fees"] is not second["fees"]
    assert first["charges"] is not second["charges"]
    assert first["metadata"] is not second["metadata"]
    assert (
        first["source_amount"]
        is not second["source_amount"]
    )
    assert (
        first["total_debit_amount"]
        is not second["total_debit_amount"]
    )


def test_pricing_values_contain_no_runtime_authority() -> None:
    for value_type in (
        TransferFee,
        TransferCharge,
        TransferAmountBreakdown,
    ):
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "collect",
            "charge_wallet",
            "debit",
            "credit",
            "post",
            "settle",
            "execute",
            "convert",
            "lock_rate",
            "fetch",
            "connect",
            "save",
            "persist",
            "repository",
            "database",
        ):
            assert forbidden not in names


def test_pricing_fields_contain_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(
            TransferAmountBreakdown
        )
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "settlement_engine",
        "provider_client",
        "fx_engine",
        "database",
    ):
        assert forbidden not in field_names


def test_pricing_domain_is_exported_from_domain() -> None:
    import afritech.novapay.domain as domain

    for symbol in (
        "TransferFeeType",
        "TransferFee",
        "TransferCharge",
        "TransferPricingMetadata",
        "TransferAmountBreakdown",
    ):
        assert hasattr(domain, symbol)
