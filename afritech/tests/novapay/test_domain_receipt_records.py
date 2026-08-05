from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from typing import Any

import pytest

import afritech.novapay.domain.receipt as receipt
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.receipt import (
    ReceiptAdjustment,
    ReceiptAdjustmentId,
    ReceiptAdjustmentType,
    ReceiptLineItem,
    ReceiptLineItemId,
    ReceiptLineItemType,
    ReceiptMetadata,
    ReceiptMonetarySummary,
    ReceiptParty,
    ReceiptPartyId,
    ReceiptPartyType,
    ReceiptTax,
    ReceiptTaxId,
    ReceiptTaxType,
)


def money(
    amount: str,
    currency: str = "AUD",
) -> Money:
    return Money.of(
        amount=amount,
        currency=currency,
    )


def party(
    party_id: str = "party-001",
    *,
    party_type: ReceiptPartyType | str = (
        ReceiptPartyType.ISSUER
    ),
    display_name: str = "NovaPay",
    external_reference: str | None = "business-001",
    metadata: object = None,
) -> ReceiptParty:
    return ReceiptParty(
        party_id=party_id,
        party_type=party_type,
        display_name=display_name,
        external_reference=external_reference,
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


def line_item(
    line_item_id: str = "line-001",
    *,
    quantity: str = "2",
    unit_amount: Money | None = None,
    total_amount: Money | None = None,
    currency: str = "AUD",
    metadata: object = None,
) -> ReceiptLineItem:
    return ReceiptLineItem(
        line_item_id=line_item_id,
        line_item_type="service",
        description="Service charge",
        quantity=quantity,
        unit_amount=(
            money("10.00", currency)
            if unit_amount is None
            else unit_amount
        ),
        total_amount=(
            money("20.00", currency)
            if total_amount is None
            else total_amount
        ),
        product_reference="service-001",
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


def adjustment(
    adjustment_id: str = "adjustment-001",
    *,
    amount: Money | None = None,
    metadata: object = None,
) -> ReceiptAdjustment:
    return ReceiptAdjustment(
        adjustment_id=adjustment_id,
        adjustment_type="surcharge",
        description="Service surcharge",
        amount=(
            money("2.00")
            if amount is None
            else amount
        ),
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


def tax(
    tax_id: str = "tax-001",
    *,
    amount: Money | None = None,
    rate: str = "10",
    metadata: object = None,
) -> ReceiptTax:
    return ReceiptTax(
        tax_id=tax_id,
        tax_type="gst",
        description="Goods and services tax",
        jurisdiction="au",
        rate=rate,
        amount=(
            money("2.00")
            if amount is None
            else amount
        ),
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


def summary(
    *,
    currency: str = "AUD",
    subtotal: str = "20.00",
    adjustment_total: str = "2.00",
    tax_total: str = "2.00",
    gross_total: str = "24.00",
    net_total: str = "24.00",
    paid_amount: str = "20.00",
    outstanding_amount: str = "4.00",
) -> ReceiptMonetarySummary:
    return ReceiptMonetarySummary(
        currency_code=currency,
        subtotal=money(
            subtotal,
            currency,
        ),
        adjustment_total=money(
            adjustment_total,
            currency,
        ),
        tax_total=money(
            tax_total,
            currency,
        ),
        gross_total=money(
            gross_total,
            currency,
        ),
        net_total=money(
            net_total,
            currency,
        ),
        paid_amount=money(
            paid_amount,
            currency,
        ),
        outstanding_amount=money(
            outstanding_amount,
            currency,
        ),
    )


def test_module_exposes_detailed_record_inventory() -> None:
    expected = {
        "ReceiptParty",
        "ReceiptLineItem",
        "ReceiptAdjustment",
        "ReceiptTax",
        "ReceiptMonetarySummary",
    }

    assert expected.issubset(
        set(receipt.__all__)
    )

    for symbol in expected:
        assert hasattr(receipt, symbol)


@pytest.mark.parametrize(
    ("record_type", "expected_fields"),
    [
        (
            ReceiptParty,
            [
                "party_id",
                "party_type",
                "display_name",
                "external_reference",
                "metadata",
            ],
        ),
        (
            ReceiptLineItem,
            [
                "line_item_id",
                "line_item_type",
                "description",
                "quantity",
                "unit_amount",
                "total_amount",
                "product_reference",
                "metadata",
            ],
        ),
        (
            ReceiptAdjustment,
            [
                "adjustment_id",
                "adjustment_type",
                "description",
                "amount",
                "metadata",
            ],
        ),
        (
            ReceiptTax,
            [
                "tax_id",
                "tax_type",
                "description",
                "jurisdiction",
                "rate",
                "amount",
                "metadata",
            ],
        ),
        (
            ReceiptMonetarySummary,
            [
                "currency_code",
                "subtotal",
                "adjustment_total",
                "tax_total",
                "gross_total",
                "net_total",
                "paid_amount",
                "outstanding_amount",
            ],
        ),
    ],
)
def test_record_field_inventory(
    record_type: type,
    expected_fields: list[str],
) -> None:
    assert [
        item.name
        for item in fields(record_type)
    ] == expected_fields


@pytest.mark.parametrize(
    "record",
    [
        party(),
        line_item(),
        adjustment(),
        tax(),
        summary(),
    ],
)
def test_detailed_records_are_immutable(
    record: object,
) -> None:
    field_name = fields(record)[0].name

    with pytest.raises(FrozenInstanceError):
        setattr(
            record,
            field_name,
            None,
        )


def test_party_normalizes_identity_and_role() -> None:
    record = party(
        party_id=" party-001 ",
        party_type=" issuer ",
        display_name=" NovaPay ",
        external_reference=" business-001 ",
    )

    assert record.party_id == ReceiptPartyId(
        "party-001"
    )
    assert (
        record.party_type
        is ReceiptPartyType.ISSUER
    )
    assert record.display_name == "NovaPay"
    assert (
        record.external_reference
        == "business-001"
    )


@pytest.mark.parametrize(
    "party_type",
    [
        ReceiptPartyType.ISSUER,
        ReceiptPartyType.RECIPIENT,
        "issuer",
        "recipient",
    ],
)
def test_party_accepts_supported_roles(
    party_type: ReceiptPartyType | str,
) -> None:
    record = party(
        party_type=party_type,
    )

    assert isinstance(
        record.party_type,
        ReceiptPartyType,
    )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\n",
    ],
)
def test_party_rejects_missing_display_name(
    invalid: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="display name",
    ):
        party(
            display_name=invalid,
        )


def test_party_allows_missing_external_reference() -> None:
    record = party(
        external_reference=None,
    )

    assert record.external_reference is None


def test_party_metadata_serialization_is_isolated() -> None:
    record = party(
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = record.canonical_dict()
    payload["metadata"]["nested"]["values"].append(3)

    fresh = record.canonical_dict()

    assert (
        fresh["metadata"]["nested"]["values"]
        == [1, 2]
    )


def test_line_item_normalizes_core_fields() -> None:
    record = ReceiptLineItem(
        line_item_id=" line-001 ",
        line_item_type=" service ",
        description=" Service charge ",
        quantity="2",
        unit_amount=money("10.00"),
        total_amount=money("20.00"),
        product_reference=" service-001 ",
        metadata={},
    )

    assert record.line_item_id == ReceiptLineItemId(
        "line-001"
    )
    assert (
        record.line_item_type
        is ReceiptLineItemType.SERVICE
    )
    assert record.description == "Service charge"
    assert record.quantity == Decimal("2")
    assert record.product_reference == "service-001"


@pytest.mark.parametrize(
    "invalid",
    [
        "0",
        "-1",
        "-0.01",
    ],
)
def test_line_item_rejects_non_positive_quantity(
    invalid: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        line_item(
            quantity=invalid,
            total_amount=money("0.00"),
        )


def test_line_item_rejects_total_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="must equal",
    ):
        line_item(
            quantity="2",
            unit_amount=money("10.00"),
            total_amount=money("19.99"),
        )


def test_line_item_rejects_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="currency",
    ):
        line_item(
            unit_amount=money(
                "10.00",
                "AUD",
            ),
            total_amount=money(
                "20.00",
                "USD",
            ),
        )


@pytest.mark.parametrize(
    ("quantity", "unit", "expected_total"),
    [
        (
            "1",
            "10.00",
            "10.00",
        ),
        (
            "2",
            "10.00",
            "20.00",
        ),
        (
            "2.5",
            "4.00",
            "10.00",
        ),
    ],
)
def test_line_item_accepts_exact_totals(
    quantity: str,
    unit: str,
    expected_total: str,
) -> None:
    record = line_item(
        quantity=quantity,
        unit_amount=money(unit),
        total_amount=money(expected_total),
    )

    assert record.quantity == Decimal(quantity)


def test_line_item_serializes_money_records() -> None:
    payload = line_item().canonical_dict()

    assert payload["line_item_id"] == "line-001"
    assert payload["line_item_type"] == "service"

    assert payload["unit_amount"] == {
        "amount": "10.00",
        "currency": "AUD",
    }

    assert payload["total_amount"] == {
        "amount": "20.00",
        "currency": "AUD",
    }


def test_line_item_metadata_serialization_is_isolated() -> None:
    record = line_item(
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = record.canonical_dict()
    payload["metadata"]["nested"]["values"].append(3)

    fresh = record.canonical_dict()

    assert (
        fresh["metadata"]["nested"]["values"]
        == [1, 2]
    )


def test_line_item_money_payload_is_isolated() -> None:
    record = line_item()

    payload = record.canonical_dict()
    payload["unit_amount"]["amount"] = "999.00"

    fresh = record.canonical_dict()

    assert fresh["unit_amount"]["amount"] == "10.00"


def test_adjustment_normalizes_identity_and_type() -> None:
    record = ReceiptAdjustment(
        adjustment_id=" adjustment-001 ",
        adjustment_type=" surcharge ",
        description=" Service surcharge ",
        amount=money("2.00"),
        metadata={},
    )

    assert record.adjustment_id == ReceiptAdjustmentId(
        "adjustment-001"
    )
    assert (
        record.adjustment_type
        is ReceiptAdjustmentType.SURCHARGE
    )
    assert record.description == "Service surcharge"


@pytest.mark.parametrize(
    "amount",
    [
        "-0.01",
        "-1.00",
    ],
)
def test_adjustment_rejects_negative_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        adjustment(
            amount=money(amount),
        )


def test_adjustment_accepts_zero_amount() -> None:
    record = adjustment(
        amount=money("0.00"),
    )

    assert record.canonical_dict()["amount"] == {
        "amount": "0.00",
        "currency": "AUD",
    }


def test_adjustment_metadata_serialization_is_isolated() -> None:
    record = adjustment(
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = record.canonical_dict()
    payload["metadata"]["nested"]["values"].append(3)

    fresh = record.canonical_dict()

    assert (
        fresh["metadata"]["nested"]["values"]
        == [1, 2]
    )


def test_tax_normalizes_identity_type_and_jurisdiction() -> None:
    record = tax(
        tax_id=" tax-001 ",
    )

    assert record.tax_id == ReceiptTaxId(
        "tax-001"
    )
    assert record.tax_type is ReceiptTaxType.GST
    assert record.jurisdiction == "au"

    payload = record.canonical_dict()

    assert payload["jurisdiction"] == "au"
    assert record.rate == Decimal("10")


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_tax_rejects_blank_jurisdiction(
    invalid: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="jurisdiction",
    ):
        ReceiptTax(
            tax_id="tax-001",
            tax_type="gst",
            description="GST",
            jurisdiction=invalid,
            rate="10",
            amount=money("2.00"),
            metadata={},
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("A", "A"),
        (" AUS ", "AUS"),
        ("12", "12"),
        (" au ", "au"),
        ("Victoria", "Victoria"),
    ],
)
def test_tax_accepts_non_empty_jurisdiction_values(
    raw: str,
    expected: str,
) -> None:
    record = ReceiptTax(
        tax_id="tax-001",
        tax_type="gst",
        description="GST",
        jurisdiction=raw,
        rate="10",
        amount=money("2.00"),
        metadata={},
    )

    assert record.jurisdiction == expected

    payload = record.canonical_dict()

    assert payload["jurisdiction"] == expected


@pytest.mark.parametrize(
    "invalid",
    [
        "-1",
        "-0.01",
        "0",
        "0.00",
    ],
)
def test_tax_rejects_non_positive_rate(
    invalid: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        tax(
            rate=invalid,
        )


@pytest.mark.parametrize(
    "valid",
    [
        "0.01",
        "1",
        "10",
        "100.5",
    ],
)
def test_tax_accepts_positive_rate(
    valid: str,
) -> None:
    record = tax(
        rate=valid,
    )

    assert record.rate == Decimal(valid)


def test_tax_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        tax(
            amount=money("-0.01"),
        )


def test_tax_metadata_serialization_is_isolated() -> None:
    record = tax(
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = record.canonical_dict()
    payload["metadata"]["nested"]["values"].append(3)

    fresh = record.canonical_dict()

    assert (
        fresh["metadata"]["nested"]["values"]
        == [1, 2]
    )


def test_summary_normalizes_currency() -> None:
    record = summary(
        currency="aud",
    )

    assert record.currency_code == "AUD"


def test_summary_accepts_balanced_values() -> None:
    record = summary()

    assert record.subtotal == money("20.00")
    assert record.adjustment_total == money("2.00")
    assert record.tax_total == money("2.00")
    assert record.gross_total == money("24.00")
    assert record.net_total == money("24.00")
    assert record.paid_amount == money("20.00")
    assert record.outstanding_amount == money(
        "4.00"
    )


def test_summary_preserves_supplied_gross_total() -> None:
    record = summary(
        gross_total="23.99",
    )

    assert record.gross_total == money("23.99")

    payload = record.canonical_dict()

    assert payload["gross_total"] == {
        "amount": "23.99",
        "currency": "AUD",
    }


def test_summary_rejects_paid_amount_exceeding_net() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        summary(
            paid_amount="25.00",
            outstanding_amount="0.00",
        )


def test_summary_rejects_paid_outstanding_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="must equal net total",
    ):
        summary(
            paid_amount="20.00",
            outstanding_amount="3.00",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "subtotal",
        "adjustment_total",
        "tax_total",
        "gross_total",
        "net_total",
        "paid_amount",
        "outstanding_amount",
    ],
)
def test_summary_rejects_currency_mismatch(
    field_name: str,
) -> None:
    values: dict[str, Any] = {
        "currency_code": "AUD",
        "subtotal": money("20.00"),
        "adjustment_total": money("2.00"),
        "tax_total": money("2.00"),
        "gross_total": money("24.00"),
        "net_total": money("24.00"),
        "paid_amount": money("20.00"),
        "outstanding_amount": money("4.00"),
    }

    original_money = values[field_name]

    assert isinstance(
        original_money,
        Money,
    )

    values[field_name] = money(
        str(original_money.amount),
        "USD",
    )

    with pytest.raises(
        ValueError,
        match="currency",
    ):
        ReceiptMonetarySummary(**values)


@pytest.mark.parametrize(
    "record",
    [
        party(),
        line_item(),
        adjustment(),
        tax(),
        summary(),
    ],
)
def test_record_serialization_is_deterministic(
    record: object,
) -> None:
    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first == second


@pytest.mark.parametrize(
    "record",
    [
        party(),
        line_item(),
        adjustment(),
        tax(),
        summary(),
    ],
)
def test_record_serialization_is_fresh(
    record: object,
) -> None:
    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first is not second


@pytest.mark.parametrize(
    "record_type",
    [
        ReceiptParty,
        ReceiptLineItem,
        ReceiptAdjustment,
        ReceiptTax,
        ReceiptMonetarySummary,
    ],
)
def test_records_add_no_runtime_authority(
    record_type: type,
) -> None:
    forbidden = {
        "execute",
        "pay",
        "transfer",
        "settle",
        "authorize",
        "reserve",
        "debit",
        "credit",
        "post",
        "submit",
        "send",
        "deliver",
        "persist",
        "save",
        "sign",
        "verify_external",
        "repository",
        "database",
    }

    names = {
        name
        for name in dir(record_type)
        if not name.startswith("__")
    }

    assert forbidden.isdisjoint(names)


def test_detailed_records_remain_internal() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain

    for symbol in (
        "ReceiptParty",
        "ReceiptLineItem",
        "ReceiptAdjustment",
        "ReceiptTax",
        "ReceiptMonetarySummary",
    ):
        assert not hasattr(domain, symbol)
        assert not hasattr(novapay, symbol)
        assert symbol not in domain.__all__
        assert symbol not in novapay.__all__


def test_receipt_integrity_evidence_is_present() -> None:
    assert hasattr(
        receipt,
        "ReceiptIntegrityEvidence",
    )

    assert (
        "ReceiptIntegrityEvidence"
        in receipt.__all__
    )


def test_receipt_verification_result_is_present() -> None:
    assert hasattr(
        receipt,
        "ReceiptVerificationResult",
    )

    assert (
        "ReceiptVerificationResult"
        in receipt.__all__
    )


def test_remaining_deferred_receipt_symbols_are_absent() -> None:
    for symbol in (
        "ReceiptPresentationSummary",
    ):
        assert not hasattr(
            receipt,
            symbol,
        )

        assert symbol not in receipt.__all__

def test_receipt_lifecycle_methods_are_present() -> None:
    for method_name in (
        "prepare",
        "issue",
        "mark_delivered",
        "cancel",
        "void",
        "expire",
        "supersede",
        "update_metadata",
    ):
        assert hasattr(
            receipt.Receipt,
            method_name,
        )
        assert callable(
            getattr(
                receipt.Receipt,
                method_name,
            )
        )
