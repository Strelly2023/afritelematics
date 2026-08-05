from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.receipt as receipt
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.receipt import (
    Receipt,
    ReceiptAdjustment,
    ReceiptAdjustmentId,
    ReceiptAdjustmentType,
    ReceiptFormat,
    ReceiptId,
    ReceiptLineItem,
    ReceiptLineItemId,
    ReceiptLineItemType,
    ReceiptMetadata,
    ReceiptParty,
    ReceiptPartyId,
    ReceiptPartyType,
    ReceiptReference,
    ReceiptReferenceType,
    ReceiptStatus,
    ReceiptTax,
    ReceiptTaxId,
    ReceiptTaxType,
    ReceiptType,
)


CREATED_AT = datetime(
    2026,
    8,
    4,
    12,
    0,
    tzinfo=timezone.utc,
)


EXPECTED_FIELDS = [
    "receipt_id",
    "receipt_type",
    "status",
    "format",
    "issuer",
    "recipient",
    "currency_code",
    "line_items",
    "adjustments",
    "taxes",
    "monetary_summary",
    "references",
    "integrity_evidence",
    "issued_at",
    "delivered_at",
    "expires_at",
    "created_at",
    "updated_at",
    "version",
    "metadata",
]


DEFERRED_SYMBOLS = [
    "ReceiptPresentationSummary",
]


DOMAIN_PUBLIC_SYMBOLS = [
    "ReceiptIntegrityEvidence",
    "ReceiptVerificationResult",
]

INTERNAL_ONLY_SYMBOLS = [
    symbol
    for symbol in receipt.__all__
    if symbol not in DOMAIN_PUBLIC_SYMBOLS
]

DEFERRED_METHODS = [
    "prepare",
    "issue",
    "mark_delivered",
    "void",
    "cancel",
    "expire",
    "supersede",
    "update_metadata",
]



def money(
    amount: str,
    currency: str = "AUD",
) -> Money:
    return Money.of(
        amount=amount,
        currency=currency,
    )


def issuer_party(
    party_id: str = "issuer-001",
) -> ReceiptParty:
    return ReceiptParty(
        party_id=party_id,
        party_type=ReceiptPartyType.ISSUER,
        display_name=party_id,
        external_reference=None,
        metadata={},
    )


def recipient_party(
    party_id: str = "recipient-001",
) -> ReceiptParty:
    return ReceiptParty(
        party_id=party_id,
        party_type=ReceiptPartyType.RECIPIENT,
        display_name=party_id,
        external_reference=None,
        metadata={},
    )


def line_item(
    line_item_id: str = "line-001",
    *,
    currency: str = "AUD",
) -> ReceiptLineItem:
    return ReceiptLineItem(
        line_item_id=line_item_id,
        line_item_type=ReceiptLineItemType.SERVICE,
        description="Service",
        quantity="1",
        unit_amount=money(
            "10.00",
            currency,
        ),
        total_amount=money(
            "10.00",
            currency,
        ),
        product_reference=None,
        metadata={},
    )


def adjustment(
    adjustment_id: str = "adjustment-001",
    *,
    currency: str = "AUD",
) -> ReceiptAdjustment:
    return ReceiptAdjustment(
        adjustment_id=adjustment_id,
        adjustment_type=(
            ReceiptAdjustmentType.SURCHARGE
        ),
        description="Surcharge",
        amount=money(
            "1.00",
            currency,
        ),
        metadata={},
    )


def tax(
    tax_id: str = "tax-001",
    *,
    currency: str = "AUD",
) -> ReceiptTax:
    return ReceiptTax(
        tax_id=tax_id,
        tax_type=ReceiptTaxType.GST,
        description="GST",
        jurisdiction="AU",
        rate="10",
        amount=money(
            "1.00",
            currency,
        ),
        metadata={},
    )


def valid_values() -> dict[str, Any]:
    return {
        "receipt_id": "receipt-001",
        "receipt_type": "payment",
        "status": "draft",
        "format": "structured",
        "issuer": issuer_party(),
        "recipient": recipient_party(),
        "currency_code": "AUD",
        "line_items": (),
        "adjustments": (),
        "taxes": (),
        "monetary_summary": None,
        "references": (),
        "integrity_evidence": (),
        "issued_at": None,
        "delivered_at": None,
        "expires_at": None,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "version": 1,
        "metadata": {},
    }


def construct_receipt(
    **overrides: Any,
) -> Receipt:
    values = valid_values()
    values.update(overrides)

    return Receipt(**values)


def test_receipt_is_in_module_inventory() -> None:
    assert "Receipt" in receipt.__all__


def test_receipt_module_inventory_count() -> None:
    assert len(receipt.__all__) == 25
def test_receipt_module_inventory_is_sorted() -> None:
    assert receipt.__all__ == sorted(
        receipt.__all__
    )


def test_receipt_module_inventory_is_unique() -> None:
    assert len(receipt.__all__) == len(
        set(receipt.__all__)
    )


def test_receipt_aggregate_field_inventory() -> None:
    assert [
        item.name
        for item in fields(Receipt)
    ] == EXPECTED_FIELDS


def test_receipt_aggregate_has_twenty_fields() -> None:
    assert len(fields(Receipt)) == 20


def test_factory_creates_draft_receipt() -> None:
    aggregate = Receipt.create(
        receipt_id=" receipt-001 ",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        recipient="recipient-001",
        currency_code="aud",
        created_at=CREATED_AT,
    )

    assert aggregate.receipt_id == ReceiptId(
        "receipt-001"
    )
    assert aggregate.receipt_type is ReceiptType.PAYMENT
    assert aggregate.status is ReceiptStatus.DRAFT
    assert aggregate.format is ReceiptFormat.STRUCTURED
    assert isinstance(
        aggregate.issuer,
        ReceiptParty,
    )
    assert aggregate.issuer.party_id == ReceiptPartyId(
        "issuer-001"
    )
    assert (
        aggregate.issuer.party_type
        is ReceiptPartyType.ISSUER
    )

    assert isinstance(
        aggregate.recipient,
        ReceiptParty,
    )
    assert aggregate.recipient.party_id == ReceiptPartyId(
        "recipient-001"
    )
    assert (
        aggregate.recipient.party_type
        is ReceiptPartyType.RECIPIENT
    )
    assert aggregate.currency_code == "AUD"
    assert aggregate.created_at == CREATED_AT
    assert aggregate.updated_at == CREATED_AT
    assert aggregate.version == 1


def test_factory_creates_empty_deferred_collections() -> None:
    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        currency_code="AUD",
        created_at=CREATED_AT,
    )

    assert aggregate.line_items == ()
    assert aggregate.adjustments == ()
    assert aggregate.taxes == ()
    assert aggregate.monetary_summary is None
    assert aggregate.references == ()
    assert aggregate.integrity_evidence == ()
    assert aggregate.issued_at is None
    assert aggregate.delivered_at is None


def test_factory_allows_optional_recipient_absence() -> None:
    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="fee",
        format="text",
        issuer="issuer-001",
        recipient=None,
        currency_code="AUD",
        created_at=CREATED_AT,
    )

    assert aggregate.recipient is None


def test_factory_normalizes_reference_collection() -> None:
    reference = ReceiptReference.create(
        reference_type="transaction",
        reference_value=" tx-001 ",
    )

    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        currency_code="AUD",
        created_at=CREATED_AT,
        references=[reference],
    )

    assert aggregate.references == (reference,)


def test_factory_normalizes_metadata() -> None:
    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        currency_code="AUD",
        created_at=CREATED_AT,
        metadata={
            "Source System": "novapay",
        },
    )

    assert aggregate.metadata == ReceiptMetadata.of(
        {
            "source_system": "novapay",
        }
    )


def test_factory_normalizes_timezone_to_utc() -> None:
    source = datetime(
        2026,
        8,
        4,
        22,
        0,
        tzinfo=timezone(timedelta(hours=10)),
    )

    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        currency_code="AUD",
        created_at=source,
    )

    assert aggregate.created_at == CREATED_AT
    assert aggregate.updated_at == CREATED_AT


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("aud", "AUD"),
        ("Usd", "USD"),
        (" eur ", "EUR"),
    ],
)
def test_factory_normalizes_currency(
    source: str,
    expected: str,
) -> None:
    aggregate = Receipt.create(
        receipt_id="receipt-001",
        receipt_type="payment",
        format="structured",
        issuer="issuer-001",
        currency_code=source,
        created_at=CREATED_AT,
    )

    assert aggregate.currency_code == expected


def test_direct_construction_normalizes_identifiers() -> None:
    issuer = ReceiptParty(
        party_id=" issuer-001 ",
        party_type="issuer",
        display_name="Issuer",
        external_reference=None,
        metadata={},
    )

    recipient = ReceiptParty(
        party_id=" recipient-001 ",
        party_type="recipient",
        display_name="Recipient",
        external_reference=None,
        metadata={},
    )

    first_line = ReceiptLineItem(
        line_item_id=" line-001 ",
        line_item_type="service",
        description="First service",
        quantity="1",
        unit_amount=money("10.00"),
        total_amount=money("10.00"),
        product_reference=None,
        metadata={},
    )

    second_line = ReceiptLineItem(
        line_item_id=" line-002 ",
        line_item_type="service",
        description="Second service",
        quantity="1",
        unit_amount=money("10.00"),
        total_amount=money("10.00"),
        product_reference=None,
        metadata={},
    )

    adjustment_record = ReceiptAdjustment(
        adjustment_id=" adjustment-001 ",
        adjustment_type="surcharge",
        description="Surcharge",
        amount=money("1.00"),
        metadata={},
    )

    tax_record = ReceiptTax(
        tax_id=" tax-001 ",
        tax_type="gst",
        description="GST",
        jurisdiction="AU",
        rate="10",
        amount=money("1.00"),
        metadata={},
    )

    aggregate = construct_receipt(
        receipt_id=" receipt-001 ",
        issuer=issuer,
        recipient=recipient,
        line_items=[
            first_line,
            second_line,
        ],
        adjustments=[
            adjustment_record,
        ],
        taxes=[
            tax_record,
        ],
        integrity_evidence=[
            " evidence-001 ",
        ],
    )

    assert aggregate.receipt_id == ReceiptId(
        "receipt-001"
    )
    assert aggregate.issuer.party_id == ReceiptPartyId(
        "issuer-001"
    )
    assert aggregate.recipient is not None
    assert aggregate.recipient.party_id == ReceiptPartyId(
        "recipient-001"
    )
    assert aggregate.line_items == (
        first_line,
        second_line,
    )
    assert aggregate.adjustments == (
        adjustment_record,
    )
    assert aggregate.taxes == (
        tax_record,
    )
    assert aggregate.integrity_evidence == (
        "evidence-001",
    )


def test_direct_construction_normalizes_enums() -> None:
    aggregate = construct_receipt(
        receipt_type="merchant payment",
        status="prepared",
        format="digital-wallet",
    )

    assert (
        aggregate.receipt_type
        is ReceiptType.MERCHANT_PAYMENT
    )
    assert aggregate.status is ReceiptStatus.PREPARED
    assert (
        aggregate.format
        is ReceiptFormat.DIGITAL_WALLET
    )


def test_direct_construction_supports_issued_state() -> None:
    issued_at = CREATED_AT + timedelta(minutes=1)

    aggregate = construct_receipt(
        status="issued",
        issued_at=issued_at,
        updated_at=issued_at,
        version=2,
    )

    assert aggregate.status is ReceiptStatus.ISSUED
    assert aggregate.issued_at == issued_at
    assert aggregate.delivered_at is None
    assert aggregate.version == 2


def test_direct_construction_supports_delivered_state() -> None:
    issued_at = CREATED_AT + timedelta(minutes=1)
    delivered_at = issued_at + timedelta(minutes=1)

    aggregate = construct_receipt(
        status="delivered",
        issued_at=issued_at,
        delivered_at=delivered_at,
        updated_at=delivered_at,
        version=3,
    )

    assert aggregate.status is ReceiptStatus.DELIVERED
    assert aggregate.issued_at == issued_at
    assert aggregate.delivered_at == delivered_at
    assert aggregate.version == 3


@pytest.mark.parametrize(
    "status",
    [
        ReceiptStatus.VOIDED,
        ReceiptStatus.SUPERSEDED,
    ],
)
def test_direct_construction_supports_terminal_issued_states(
    status: ReceiptStatus,
) -> None:
    issued_at = CREATED_AT + timedelta(minutes=1)

    aggregate = construct_receipt(
        status=status,
        issued_at=issued_at,
        updated_at=issued_at,
        version=2,
    )

    assert aggregate.status is status
    assert aggregate.is_terminal


@pytest.mark.parametrize(
    "status",
    [
        ReceiptStatus.CANCELED,
        ReceiptStatus.EXPIRED,
    ],
)
def test_direct_construction_supports_terminal_non_issued_states(
    status: ReceiptStatus,
) -> None:
    aggregate = construct_receipt(
        status=status,
    )

    assert aggregate.status is status
    assert aggregate.issued_at is None
    assert aggregate.is_terminal


@pytest.mark.parametrize(
    "status",
    [
        ReceiptStatus.DRAFT,
        ReceiptStatus.PREPARED,
        ReceiptStatus.ISSUED,
        ReceiptStatus.DELIVERED,
    ],
)
def test_non_terminal_classification(
    status: ReceiptStatus,
) -> None:
    issued_at = (
        CREATED_AT + timedelta(minutes=1)
        if status.is_issued
        else None
    )

    delivered_at = (
        CREATED_AT + timedelta(minutes=2)
        if status is ReceiptStatus.DELIVERED
        else None
    )

    aggregate = construct_receipt(
        status=status,
        issued_at=issued_at,
        delivered_at=delivered_at,
        updated_at=(
            delivered_at
            or issued_at
            or CREATED_AT
        ),
    )

    assert not aggregate.is_terminal


def test_receipt_is_frozen() -> None:
    aggregate = construct_receipt()

    with pytest.raises(FrozenInstanceError):
        aggregate.version = 2


def test_collection_fields_are_tuples() -> None:
    line_record = line_item("line-001")
    adjustment_record = adjustment("adjustment-001")
    tax_record = tax("tax-001")

    aggregate = construct_receipt(
        line_items=[line_record],
        adjustments=[adjustment_record],
        taxes=[tax_record],
        references=[
            ReceiptReference.create(
                reference_type="transaction",
                reference_value="tx-001",
            )
        ],
        integrity_evidence=["evidence-001"],
    )

    assert isinstance(aggregate.line_items, tuple)
    assert isinstance(aggregate.adjustments, tuple)
    assert isinstance(aggregate.taxes, tuple)
    assert isinstance(aggregate.references, tuple)
    assert isinstance(
        aggregate.integrity_evidence,
        tuple,
    )

    assert aggregate.line_items == (
        line_record,
    )
    assert aggregate.adjustments == (
        adjustment_record,
    )
    assert aggregate.taxes == (
        tax_record,
    )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "AU",
        "AUDD",
        "12A",
        "A$D",
    ],
)
def test_rejects_invalid_currency_text(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        construct_receipt(
            currency_code=invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        1,
        True,
        object(),
    ],
)
def test_rejects_invalid_currency_type(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        construct_receipt(
            currency_code=invalid,
        )


def test_rejects_identical_issuer_and_recipient() -> None:
    issuer = issuer_party("party-001")
    recipient = recipient_party("party-001")

    assert issuer.party_id == recipient.party_id
    assert issuer.party_type is ReceiptPartyType.ISSUER
    assert (
        recipient.party_type
        is ReceiptPartyType.RECIPIENT
    )

    with pytest.raises(
        ValueError,
        match="must differ",
    ):
        construct_receipt(
            issuer=issuer,
            recipient=recipient,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "values",
        "expected_message",
    ),
    [
        (
            "line_items",
            [
                line_item("line-001"),
                line_item("line-001"),
            ],
            "must not contain duplicate identifiers",
        ),
        (
            "adjustments",
            [
                adjustment("adjustment-001"),
                adjustment("adjustment-001"),
            ],
            "must not contain duplicate identifiers",
        ),
        (
            "taxes",
            [
                tax("tax-001"),
                tax("tax-001"),
            ],
            "must not contain duplicate identifiers",
        ),
        (
            "integrity_evidence",
            [
                "evidence-001",
                "evidence-001",
            ],
            "must not contain duplicates",
        ),
    ],
)
def test_rejects_duplicate_collection_values(
    field_name: str,
    values: list[Any],
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        construct_receipt(
            **{
                field_name: values,
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "line_items",
        "adjustments",
        "taxes",
        "integrity_evidence",
    ],
)
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "value",
        {"value": "x"},
        object(),
    ],
)
def test_rejects_invalid_collection_type(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        construct_receipt(
            **{
                field_name: invalid,
            }
        )


def test_rejects_duplicate_references() -> None:
    reference = ReceiptReference.create(
        reference_type="transaction",
        reference_value="tx-001",
    )

    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        construct_receipt(
            references=[
                reference,
                reference,
            ]
        )


def test_rejects_non_reference_collection_member() -> None:
    with pytest.raises(
        TypeError,
        match="ReceiptReference",
    ):
        construct_receipt(
            references=[
                "transaction-001",
            ]
        )


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "reference",
        {"reference": "tx-001"},
        object(),
    ],
)
def test_rejects_invalid_reference_collection_type(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        construct_receipt(
            references=invalid,
        )


def test_rejects_invalid_monetary_summary_type() -> None:
    with pytest.raises(
        TypeError,
        match="ReceiptMonetarySummary or None",
    ):
        construct_receipt(
            monetary_summary={},
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
        "issued_at",
        "delivered_at",
        "expires_at",
    ],
)
def test_rejects_naive_datetime(
    field_name: str,
) -> None:
    values = valid_values()

    if field_name in {
        "issued_at",
        "delivered_at",
    }:
        values["status"] = "delivered"
        values["issued_at"] = (
            CREATED_AT + timedelta(minutes=1)
        )
        values["delivered_at"] = (
            CREATED_AT + timedelta(minutes=2)
        )

    values[field_name] = datetime(
        2026,
        8,
        4,
        12,
        0,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        Receipt(**values)


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    [
        ("created_at", None),
        ("created_at", "2026-08-04"),
        ("updated_at", None),
        ("updated_at", "2026-08-04"),
        ("issued_at", "2026-08-04"),
        ("delivered_at", "2026-08-04"),
        ("expires_at", "2026-08-04"),
    ],
)
def test_rejects_invalid_datetime_type(
    field_name: str,
    invalid: object,
) -> None:
    values = valid_values()
    values[field_name] = invalid

    with pytest.raises(TypeError):
        Receipt(**values)


def test_rejects_updated_at_before_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="updated_at must not precede",
    ):
        construct_receipt(
            updated_at=(
                CREATED_AT - timedelta(seconds=1)
            ),
        )


def test_rejects_issued_at_before_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="issued_at must not precede",
    ):
        construct_receipt(
            status="issued",
            issued_at=(
                CREATED_AT - timedelta(seconds=1)
            ),
        )


def test_rejects_delivered_at_without_issued_at() -> None:
    with pytest.raises(
        ValueError,
        match="requires issued_at",
    ):
        construct_receipt(
            delivered_at=(
                CREATED_AT + timedelta(minutes=1)
            ),
        )


def test_rejects_delivered_at_before_issued_at() -> None:
    issued_at = CREATED_AT + timedelta(minutes=2)

    with pytest.raises(
        ValueError,
        match="must not precede issued_at",
    ):
        construct_receipt(
            status="delivered",
            issued_at=issued_at,
            delivered_at=(
                issued_at - timedelta(seconds=1)
            ),
        )


@pytest.mark.parametrize(
    "expires_at",
    [
        CREATED_AT,
        CREATED_AT - timedelta(seconds=1),
    ],
)
def test_rejects_invalid_expiry_chronology(
    expires_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be after created_at",
    ):
        construct_receipt(
            expires_at=expires_at,
        )


@pytest.mark.parametrize(
    "status",
    [
        ReceiptStatus.DRAFT,
        ReceiptStatus.PREPARED,
        ReceiptStatus.CANCELED,
    ],
)
def test_non_issued_status_rejects_issued_at(
    status: ReceiptStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not have issued_at",
    ):
        construct_receipt(
            status=status,
            issued_at=(
                CREATED_AT + timedelta(minutes=1)
            ),
        )


@pytest.mark.parametrize(
    "status",
    [
        ReceiptStatus.ISSUED,
        ReceiptStatus.DELIVERED,
        ReceiptStatus.VOIDED,
        ReceiptStatus.SUPERSEDED,
    ],
)
def test_issued_status_requires_issued_at(
    status: ReceiptStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires issued_at",
    ):
        construct_receipt(
            status=status,
        )


def test_delivered_status_requires_delivered_at() -> None:
    issued_at = CREATED_AT + timedelta(minutes=1)

    with pytest.raises(
        ValueError,
        match="requires delivered_at",
    ):
        construct_receipt(
            status="delivered",
            issued_at=issued_at,
            updated_at=issued_at,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        0,
        -1,
        -100,
    ],
)
def test_rejects_non_positive_version(
    invalid: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        construct_receipt(
            version=invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        1.5,
        "1",
        True,
        object(),
    ],
)
def test_rejects_invalid_version_type(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        construct_receipt(
            version=invalid,
        )


def test_serialization_contains_all_fields() -> None:
    aggregate = construct_receipt()

    assert list(
        aggregate.canonical_dict()
    ) == EXPECTED_FIELDS


def test_serialization_is_deterministic() -> None:
    aggregate = construct_receipt(
        line_items=[
            line_item("line-001"),
            line_item("line-002"),
        ],
        adjustments=[
            adjustment("adjustment-001"),
        ],
        taxes=[
            tax("tax-001"),
        ],
        references=[
            ReceiptReference.create(
                reference_type="transaction",
                reference_value="tx-001",
            ),
        ],
        integrity_evidence=[
            "evidence-001",
        ],
        metadata={
            "source": "novapay",
        },
    )

    assert (
        aggregate.canonical_dict()
        == aggregate.canonical_dict()
    )

def test_serialization_is_fresh() -> None:
    aggregate = construct_receipt(
        line_items=[
            line_item("line-001"),
        ],
        adjustments=[
            adjustment("adjustment-001"),
        ],
        taxes=[
            tax("tax-001"),
        ],
        references=[
            ReceiptReference.create(
                reference_type="transaction",
                reference_value="tx-001",
            ),
        ],
        integrity_evidence=[
            "evidence-001",
        ],
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first is not second
    assert first["line_items"] is not second["line_items"]
    assert (
        first["adjustments"]
        is not second["adjustments"]
    )
    assert first["taxes"] is not second["taxes"]
    assert (
        first["references"]
        is not second["references"]
    )
    assert (
        first["integrity_evidence"]
        is not second["integrity_evidence"]
    )
    assert first["metadata"] is not second["metadata"]
    assert (
        first["metadata"]["nested"]
        is not second["metadata"]["nested"]
    )
    assert (
        first["metadata"]["nested"]["values"]
        is not second["metadata"]["nested"]["values"]
    )

def test_serialization_mutation_does_not_affect_aggregate() -> None:
    aggregate = construct_receipt(
        line_items=[
            line_item("line-001"),
        ],
        references=[
            ReceiptReference.create(
                reference_type="transaction",
                reference_value="tx-001",
            ),
        ],
        integrity_evidence=[
            "evidence-001",
        ],
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = aggregate.canonical_dict()

    payload["line_items"].append("line-002")
    payload["references"].append(
        {
            "reference_type": "external",
            "reference_value": "external-001",
        }
    )
    payload["integrity_evidence"].append(
        "evidence-002"
    )
    payload["metadata"]["nested"]["values"].append(3)

    fresh = aggregate.canonical_dict()

    assert len(fresh["line_items"]) == 1
    assert (
        fresh["line_items"][0]["line_item_id"]
        == "line-001"
    )
    assert all(
        item != "line-002"
        for item in fresh["line_items"]
    )
    assert fresh["references"] == [
        {
            "reference_type": "transaction",
            "reference_value": "tx-001",
        }
    ]
    assert fresh["integrity_evidence"] == [
        "evidence-001",
    ]
    assert fresh["metadata"] == {
        "nested": {
            "values": [1, 2],
        },
    }

def test_serialization_normalizes_timestamps_to_iso_utc() -> None:
    aggregate = construct_receipt(
        created_at=datetime(
            2026,
            8,
            4,
            22,
            0,
            tzinfo=timezone(
                timedelta(hours=10)
            ),
        ),
        updated_at=datetime(
            2026,
            8,
            4,
            22,
            1,
            tzinfo=timezone(
                timedelta(hours=10)
            ),
        ),
    )

    payload = aggregate.canonical_dict()

    assert payload["created_at"] == (
        "2026-08-04T12:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-04T12:01:00+00:00"
    )


def test_receipt_integrity_evidence_record_is_present() -> None:
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


@pytest.mark.parametrize(
    "symbol",
    DEFERRED_SYMBOLS,
)
def test_detailed_record_symbols_remain_absent(
    symbol: str,
) -> None:
    assert not hasattr(receipt, symbol)


@pytest.mark.parametrize(
    "method",
    [
        "prepare",
        "issue",
        "mark_delivered",
        "cancel",
        "void",
        "expire",
        "supersede",
        "update_metadata",
    ],
)
def test_lifecycle_methods_are_present(
    method: str,
) -> None:
    assert hasattr(Receipt, method)
    assert callable(getattr(Receipt, method))


@pytest.mark.parametrize(
    "symbol",
    DOMAIN_PUBLIC_SYMBOLS,
)
def test_domain_public_receipt_aggregate_records_are_exported(
    symbol: str,
) -> None:
    assert hasattr(domain, symbol)
    assert symbol in domain.__all__
    assert getattr(domain, symbol) is getattr(receipt, symbol)


@pytest.mark.parametrize(
    "symbol",
    INTERNAL_ONLY_SYMBOLS,
)
def test_receipt_aggregate_remains_internal(
    symbol: str,
) -> None:
    assert not hasattr(domain, symbol)
    assert not hasattr(novapay, symbol)
    assert symbol not in domain.__all__
    assert symbol not in novapay.__all__


def test_receipt_aggregate_has_no_runtime_fields() -> None:
    forbidden = {
        "repository",
        "database",
        "provider_client",
        "payment_service",
        "transfer_service",
        "wallet_service",
        "ledger_service",
        "settlement_engine",
        "reconciliation_engine",
        "delivery_client",
        "signing_service",
        "verification_client",
    }

    field_names = {
        value.name
        for value in fields(Receipt)
    }

    assert forbidden.isdisjoint(field_names)


def test_receipt_aggregate_has_no_runtime_methods() -> None:
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
        for name in dir(Receipt)
        if not name.startswith("__")
    }

    assert forbidden.isdisjoint(names)
