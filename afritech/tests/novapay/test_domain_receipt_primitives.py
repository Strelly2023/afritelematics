from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from enum import Enum
from typing import Any

import pytest

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.receipt as receipt
from afritech.novapay.domain.receipt import (
    ReceiptAdjustmentId,
    ReceiptAdjustmentType,
    ReceiptFormat,
    ReceiptId,
    ReceiptIntegrityEvidenceType,
    ReceiptLineItemId,
    ReceiptLineItemType,
    ReceiptMetadata,
    ReceiptPartyId,
    ReceiptPartyType,
    ReceiptReference,
    ReceiptReferenceType,
    ReceiptStatus,
    ReceiptTaxId,
    ReceiptTaxType,
    ReceiptType,
    ReceiptVerificationStatus,
)


EXPECTED_ALL = [
    "Receipt",
    "ReceiptAdjustment",
    "ReceiptAdjustmentId",
    "ReceiptAdjustmentType",
    "ReceiptFormat",
    "ReceiptId",
    "ReceiptIntegrityEvidence",
    "ReceiptIntegrityEvidenceType",
    "ReceiptLineItem",
    "ReceiptLineItemId",
    "ReceiptLineItemType",
    "ReceiptMetadata",
    "ReceiptMonetarySummary",
    "ReceiptParty",
    "ReceiptPartyId",
    "ReceiptPartyType",
    "ReceiptReference",
    "ReceiptReferenceType",
    "ReceiptStatus",
    "ReceiptTax",
    "ReceiptTaxId",
    "ReceiptTaxType",
    "ReceiptType",
    "ReceiptVerificationResult",
    "ReceiptVerificationStatus",
]


DOMAIN_PUBLIC_SYMBOLS = [
    "ReceiptIntegrityEvidence",
    "ReceiptVerificationResult",
]


INTERNAL_ONLY_SYMBOLS = [
    symbol
    for symbol in EXPECTED_ALL
    if symbol not in DOMAIN_PUBLIC_SYMBOLS
]

IDENTIFIER_TYPES = [
    ReceiptId,
    ReceiptPartyId,
    ReceiptLineItemId,
    ReceiptAdjustmentId,
    ReceiptTaxId,
]


ENUM_TYPES = [
    ReceiptType,
    ReceiptStatus,
    ReceiptFormat,
    ReceiptPartyType,
    ReceiptReferenceType,
    ReceiptLineItemType,
    ReceiptAdjustmentType,
    ReceiptTaxType,
    ReceiptIntegrityEvidenceType,
    ReceiptVerificationStatus,
]


DEFERRED_SYMBOLS = [
    "ReceiptPresentationSummary",
]

def test_module_public_inventory() -> None:
    assert receipt.__all__ == EXPECTED_ALL


def test_module_inventory_is_sorted() -> None:
    assert receipt.__all__ == sorted(
        receipt.__all__
    )


def test_module_inventory_is_unique() -> None:
    assert len(receipt.__all__) == len(
        set(receipt.__all__)
    )


@pytest.mark.parametrize(
    "symbol",
    EXPECTED_ALL,
)
def test_module_owns_every_declared_symbol(
    symbol: str,
) -> None:
    assert hasattr(receipt, symbol)


def test_identifier_type_count() -> None:
    assert len(IDENTIFIER_TYPES) == 5


@pytest.mark.parametrize(
    ("identifier_type", "source", "expected"),
    [
        (
            ReceiptId,
            " receipt-001 ",
            "receipt-001",
        ),
        (
            ReceiptPartyId,
            " party/issuer-001 ",
            "party/issuer-001",
        ),
        (
            ReceiptLineItemId,
            " line-item-001 ",
            "line-item-001",
        ),
        (
            ReceiptAdjustmentId,
            " adjustment-001 ",
            "adjustment-001",
        ),
        (
            ReceiptTaxId,
            " tax-001 ",
            "tax-001",
        ),
    ],
)
def test_identifier_normalization(
    identifier_type: type[Any],
    source: str,
    expected: str,
) -> None:
    identifier = identifier_type.of(source)

    assert identifier.value == expected
    assert str(identifier) == expected


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_factory_is_idempotent(
    identifier_type: type[Any],
) -> None:
    identifier = identifier_type.of("value-001")

    assert identifier_type.of(identifier) is identifier


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_is_frozen(
    identifier_type: type[Any],
) -> None:
    identifier = identifier_type.of("value-001")

    with pytest.raises(FrozenInstanceError):
        identifier.value = "changed"


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "   ",
        "-invalid",
        "invalid-",
        "invalid value!",
    ],
)
def test_identifier_rejects_invalid_text(
    identifier_type: type[Any],
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        identifier_type.of(invalid)


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
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
def test_identifier_rejects_invalid_type(
    identifier_type: type[Any],
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        identifier_type.of(invalid)


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_rejects_excessive_length(
    identifier_type: type[Any],
) -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        identifier_type.of("a" * 129)


def test_enum_group_count() -> None:
    assert len(ENUM_TYPES) == 10


@pytest.mark.parametrize(
    ("enum_type", "source", "expected"),
    [
        (
            ReceiptType,
            "Merchant Payment",
            ReceiptType.MERCHANT_PAYMENT,
        ),
        (
            ReceiptStatus,
            "ISSUED",
            ReceiptStatus.ISSUED,
        ),
        (
            ReceiptFormat,
            "digital-wallet",
            ReceiptFormat.DIGITAL_WALLET,
        ),
        (
            ReceiptPartyType,
            "recipient",
            ReceiptPartyType.RECIPIENT,
        ),
        (
            ReceiptReferenceType,
            "settlement reconciliation",
            (
                ReceiptReferenceType
                .SETTLEMENT_RECONCILIATION
            ),
        ),
        (
            ReceiptLineItemType,
            "fee",
            ReceiptLineItemType.FEE,
        ),
        (
            ReceiptAdjustmentType,
            "surcharge",
            ReceiptAdjustmentType.SURCHARGE,
        ),
        (
            ReceiptTaxType,
            "GST",
            ReceiptTaxType.GST,
        ),
        (
            ReceiptIntegrityEvidenceType,
            "sha256 digest",
            (
                ReceiptIntegrityEvidenceType
                .SHA256_DIGEST
            ),
        ),
        (
            ReceiptVerificationStatus,
            "partially verified",
            (
                ReceiptVerificationStatus
                .PARTIALLY_VERIFIED
            ),
        ),
    ],
)
def test_enum_parsing(
    enum_type: type[Enum],
    source: str,
    expected: Enum,
) -> None:
    assert enum_type.parse(source) is expected


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
def test_enum_factory_is_idempotent(
    enum_type: type[Enum],
) -> None:
    member = tuple(enum_type)[0]

    assert enum_type.parse(member) is member


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
def test_enum_rejects_unsupported_value(
    enum_type: type[Enum],
) -> None:
    with pytest.raises(
        ValueError,
        match="unsupported",
    ):
        enum_type.parse("unsupported-value")


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
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
def test_enum_rejects_invalid_type(
    enum_type: type[Enum],
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        enum_type.parse(invalid)


@pytest.mark.parametrize(
    "terminal",
    [
        ReceiptStatus.VOIDED,
        ReceiptStatus.CANCELED,
        ReceiptStatus.EXPIRED,
        ReceiptStatus.SUPERSEDED,
    ],
)
def test_terminal_receipt_status_classification(
    terminal: ReceiptStatus,
) -> None:
    assert terminal.is_terminal


@pytest.mark.parametrize(
    "non_terminal",
    [
        ReceiptStatus.DRAFT,
        ReceiptStatus.PREPARED,
        ReceiptStatus.ISSUED,
        ReceiptStatus.DELIVERED,
    ],
)
def test_non_terminal_receipt_status_classification(
    non_terminal: ReceiptStatus,
) -> None:
    assert not non_terminal.is_terminal


@pytest.mark.parametrize(
    "issued",
    [
        ReceiptStatus.ISSUED,
        ReceiptStatus.DELIVERED,
        ReceiptStatus.VOIDED,
        ReceiptStatus.SUPERSEDED,
    ],
)
def test_issued_receipt_status_classification(
    issued: ReceiptStatus,
) -> None:
    assert issued.is_issued


@pytest.mark.parametrize(
    "not_issued",
    [
        ReceiptStatus.DRAFT,
        ReceiptStatus.PREPARED,
        ReceiptStatus.CANCELED,
        ReceiptStatus.EXPIRED,
    ],
)
def test_not_issued_receipt_status_classification(
    not_issued: ReceiptStatus,
) -> None:
    assert not not_issued.is_issued


@pytest.mark.parametrize(
    "adjustment_type",
    [
        ReceiptAdjustmentType.DISCOUNT,
        ReceiptAdjustmentType.REBATE,
        ReceiptAdjustmentType.CREDIT,
        ReceiptAdjustmentType.PROMOTION,
    ],
)
def test_reducing_adjustment_classification(
    adjustment_type: ReceiptAdjustmentType,
) -> None:
    assert adjustment_type.reduces_total


@pytest.mark.parametrize(
    "adjustment_type",
    [
        ReceiptAdjustmentType.SURCHARGE,
        ReceiptAdjustmentType.DEBIT,
    ],
)
def test_increasing_adjustment_classification(
    adjustment_type: ReceiptAdjustmentType,
) -> None:
    assert adjustment_type.increases_total


@pytest.mark.parametrize(
    "adjustment_type",
    [
        ReceiptAdjustmentType.ROUNDING,
        ReceiptAdjustmentType.CORRECTION,
    ],
)
def test_neutral_adjustment_classification(
    adjustment_type: ReceiptAdjustmentType,
) -> None:
    assert not adjustment_type.reduces_total
    assert not adjustment_type.increases_total


def test_verified_status_is_successful() -> None:
    assert ReceiptVerificationStatus.VERIFIED.is_successful


@pytest.mark.parametrize(
    "status",
    [
        ReceiptVerificationStatus.NOT_VERIFIED,
        ReceiptVerificationStatus.PARTIALLY_VERIFIED,
        ReceiptVerificationStatus.FAILED,
        ReceiptVerificationStatus.EXPIRED,
        ReceiptVerificationStatus.REVOKED,
    ],
)
def test_non_verified_status_is_not_successful(
    status: ReceiptVerificationStatus,
) -> None:
    assert not status.is_successful


@pytest.mark.parametrize(
    "status",
    [
        ReceiptVerificationStatus.PARTIALLY_VERIFIED,
        ReceiptVerificationStatus.FAILED,
        ReceiptVerificationStatus.EXPIRED,
        ReceiptVerificationStatus.REVOKED,
    ],
)
def test_verification_status_requires_attention(
    status: ReceiptVerificationStatus,
) -> None:
    assert status.requires_attention


@pytest.mark.parametrize(
    "status",
    [
        ReceiptVerificationStatus.NOT_VERIFIED,
        ReceiptVerificationStatus.VERIFIED,
    ],
)
def test_verification_status_does_not_require_attention(
    status: ReceiptVerificationStatus,
) -> None:
    assert not status.requires_attention


def test_metadata_empty_factory() -> None:
    metadata = ReceiptMetadata.empty()

    assert not metadata
    assert len(metadata) == 0
    assert metadata.canonical_dict() == {}


def test_metadata_none_factory() -> None:
    metadata = ReceiptMetadata.of(None)

    assert not metadata
    assert metadata.canonical_dict() == {}


def test_metadata_factory_is_idempotent() -> None:
    metadata = ReceiptMetadata.of(
        {"source": "novapay"}
    )

    assert ReceiptMetadata.of(metadata) is metadata


def test_metadata_normalizes_keys() -> None:
    metadata = ReceiptMetadata.of(
        {
            "Source System": "novapay",
            "Nested-Data": {
                "Reference Values": [1, 2],
            },
        }
    )

    assert metadata.canonical_dict() == {
        "nested_data": {
            "reference_values": [1, 2],
        },
        "source_system": "novapay",
    }


def test_metadata_ordering_is_deterministic() -> None:
    metadata = ReceiptMetadata.of(
        {
            "z_key": 1,
            "a_key": 2,
            "m_key": 3,
        }
    )

    assert list(
        metadata.canonical_dict()
    ) == [
        "a_key",
        "m_key",
        "z_key",
    ]


def test_metadata_isolated_from_source() -> None:
    source = {
        "nested": {
            "values": [1, 2],
        }
    }

    metadata = ReceiptMetadata.of(source)

    source["nested"]["values"].append(3)

    assert metadata.canonical_dict() == {
        "nested": {
            "values": [1, 2],
        }
    }


def test_metadata_serialization_is_fresh() -> None:
    metadata = ReceiptMetadata.of(
        {
            "nested": {
                "values": [1, 2],
            }
        }
    )

    first = metadata.canonical_dict()
    second = metadata.canonical_dict()

    assert first is not second
    assert first["nested"] is not second["nested"]
    assert (
        first["nested"]["values"]
        is not second["nested"]["values"]
    )

    first["nested"]["values"].append(3)

    assert metadata.canonical_dict() == {
        "nested": {
            "values": [1, 2],
        }
    }


def test_metadata_get_returns_fresh_value() -> None:
    metadata = ReceiptMetadata.of(
        {
            "nested": {
                "values": [1, 2],
            }
        }
    )

    first = metadata.get("nested")
    second = metadata.get("nested")

    assert first == second
    assert first is not second

    first["values"].append(3)

    assert metadata.get("nested") == {
        "values": [1, 2],
    }


def test_metadata_membership_normalizes_key() -> None:
    metadata = ReceiptMetadata.of(
        {
            "Source System": "novapay",
        }
    )

    assert "source system" in metadata
    assert "source-system" in metadata
    assert "source_system" in metadata
    assert 1 not in metadata


def test_metadata_default_is_fresh() -> None:
    metadata = ReceiptMetadata.empty()
    default = {"values": [1]}

    result = metadata.get(
        "missing",
        default,
    )

    assert result == default
    assert result is not default


def test_metadata_is_frozen() -> None:
    metadata = ReceiptMetadata.of(
        {"source": "novapay"}
    )

    with pytest.raises(FrozenInstanceError):
        metadata._values = {}


@pytest.mark.parametrize(
    "invalid",
    [
        "metadata",
        [],
        1,
        True,
        object(),
    ],
)
def test_metadata_rejects_non_mapping(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        ReceiptMetadata.of(invalid)


def test_metadata_rejects_duplicate_normalized_keys() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate normalized key",
    ):
        ReceiptMetadata.of(
            {
                "Source System": 1,
                "source_system": 2,
            }
        )


@pytest.mark.parametrize(
    "invalid_key",
    [
        "",
        " ",
        "1_invalid",
        "invalid!",
    ],
)
def test_metadata_rejects_invalid_key(
    invalid_key: str,
) -> None:
    with pytest.raises(ValueError):
        ReceiptMetadata.of(
            {
                invalid_key: "value",
            }
        )


def test_metadata_rejects_non_json_value() -> None:
    with pytest.raises(
        TypeError,
        match="JSON-compatible",
    ):
        ReceiptMetadata.of(
            {
                "value": object(),
            }
        )


def test_metadata_rejects_too_many_entries() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain more",
    ):
        ReceiptMetadata.of(
            {
                f"key_{index}": index
                for index in range(65)
            }
        )


def test_metadata_rejects_excessive_nesting() -> None:
    value: dict[str, object] = {
        "value": "leaf",
    }

    for index in range(10):
        value = {
            f"level_{index}": value,
        }

    with pytest.raises(
        ValueError,
        match="nesting exceeds",
    ):
        ReceiptMetadata.of(value)


def test_reference_construction() -> None:
    reference = ReceiptReference.create(
        reference_type="transaction",
        reference_value=" tx-001 ",
    )

    assert (
        reference.reference_type
        is ReceiptReferenceType.TRANSACTION
    )
    assert reference.reference_value == "tx-001"


def test_reference_direct_construction_normalizes() -> None:
    reference = ReceiptReference(
        reference_type="wallet",
        reference_value=" wallet-001 ",
    )

    assert (
        reference.reference_type
        is ReceiptReferenceType.WALLET
    )
    assert reference.reference_value == "wallet-001"


def test_reference_canonical_key() -> None:
    reference = ReceiptReference.create(
        reference_type="transfer",
        reference_value="transfer-001",
    )

    assert reference.canonical_key == (
        "transfer",
        "transfer-001",
    )


def test_reference_serialization() -> None:
    reference = ReceiptReference.create(
        reference_type="remittance",
        reference_value="remittance-001",
    )

    assert reference.canonical_dict() == {
        "reference_type": "remittance",
        "reference_value": "remittance-001",
    }


def test_reference_serialization_is_fresh() -> None:
    reference = ReceiptReference.create(
        reference_type="transaction",
        reference_value="transaction-001",
    )

    assert (
        reference.canonical_dict()
        is not reference.canonical_dict()
    )


def test_reference_is_frozen() -> None:
    reference = ReceiptReference.create(
        reference_type="transaction",
        reference_value="transaction-001",
    )

    with pytest.raises(FrozenInstanceError):
        reference.reference_value = "changed"


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "unsupported",
    ],
)
def test_reference_rejects_invalid_type(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        ReceiptReference.create(
            reference_type=invalid,
            reference_value="reference-001",
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
def test_reference_rejects_non_string_type(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        ReceiptReference.create(
            reference_type=invalid,
            reference_value="reference-001",
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
    ],
)
def test_reference_rejects_empty_value(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        ReceiptReference.create(
            reference_type="transaction",
            reference_value=invalid,
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
def test_reference_rejects_non_string_value(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        ReceiptReference.create(
            reference_type="transaction",
            reference_value=invalid,
        )


def test_reference_rejects_excessive_length() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ReceiptReference.create(
            reference_type="transaction",
            reference_value="a" * 257,
        )


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


@pytest.mark.parametrize(
    "symbol",
    DEFERRED_SYMBOLS,
)
def test_deferred_symbols_remain_absent(
    symbol: str,
) -> None:
    assert not hasattr(receipt, symbol)


@pytest.mark.parametrize(
    "symbol",
    DOMAIN_PUBLIC_SYMBOLS,
)
def test_domain_public_receipt_records_are_exported(
    symbol: str,
) -> None:
    assert hasattr(domain, symbol)
    assert symbol in domain.__all__
    assert getattr(domain, symbol) is getattr(receipt, symbol)


@pytest.mark.parametrize(
    "symbol",
    INTERNAL_ONLY_SYMBOLS,
)
def test_primitives_remain_internal(
    symbol: str,
) -> None:
    assert not hasattr(domain, symbol)
    assert not hasattr(novapay, symbol)
    assert symbol not in domain.__all__
    assert symbol not in novapay.__all__

def test_primitive_dataclasses_have_no_runtime_fields() -> None:
    primitive_types = [
        ReceiptId,
        ReceiptPartyId,
        ReceiptLineItemId,
        ReceiptAdjustmentId,
        ReceiptTaxId,
        ReceiptMetadata,
        ReceiptReference,
    ]

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

    for primitive_type in primitive_types:
        field_names = {
            value.name
            for value in fields(primitive_type)
        }

        assert forbidden.isdisjoint(field_names)


def test_primitives_have_no_runtime_methods() -> None:
    primitive_types = [
        ReceiptId,
        ReceiptPartyId,
        ReceiptLineItemId,
        ReceiptAdjustmentId,
        ReceiptTaxId,
        ReceiptMetadata,
        ReceiptReference,
    ]

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

    for primitive_type in primitive_types:
        names = {
            name
            for name in dir(primitive_type)
            if not name.startswith("__")
        }

        assert forbidden.isdisjoint(names)
