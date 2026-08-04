from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from afritech.novapay.domain import remittance
from afritech.novapay.domain.remittance import (
    RemittanceDirection,
    RemittanceId,
    RemittanceMetadata,
    RemittancePriority,
    RemittancePurpose,
    RemittanceReference,
    RemittanceStatus,
    RemittanceType,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("draft", RemittanceStatus.DRAFT),
        ("validated", RemittanceStatus.VALIDATED),
        ("authorized", RemittanceStatus.AUTHORIZED),
        ("submitted", RemittanceStatus.SUBMITTED),
        ("processing", RemittanceStatus.PROCESSING),
        ("in progress", RemittanceStatus.PROCESSING),
        ("completed", RemittanceStatus.COMPLETED),
        ("complete", RemittanceStatus.COMPLETED),
        ("failed", RemittanceStatus.FAILED),
        ("cancelled", RemittanceStatus.CANCELLED),
        ("canceled", RemittanceStatus.CANCELLED),
        ("expired", RemittanceStatus.EXPIRED),
        ("reversed", RemittanceStatus.REVERSED),
    ],
)
def test_remittance_status_parse(
    raw: str,
    expected: RemittanceStatus,
) -> None:
    assert RemittanceStatus.parse(raw) is expected


def test_remittance_status_inventory() -> None:
    assert tuple(
        item.value
        for item in RemittanceStatus
    ) == (
        "draft",
        "validated",
        "authorized",
        "submitted",
        "processing",
        "completed",
        "failed",
        "cancelled",
        "expired",
        "reversed",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("domestic", RemittanceType.DOMESTIC),
        (
            "domestic transfer",
            RemittanceType.DOMESTIC,
        ),
        (
            "international",
            RemittanceType.INTERNATIONAL,
        ),
        (
            "international-transfer",
            RemittanceType.INTERNATIONAL,
        ),
        (
            "cross border",
            RemittanceType.INTERNATIONAL,
        ),
        ("cash pickup", RemittanceType.CASH_PICKUP),
        (
            "bank-deposit",
            RemittanceType.BANK_DEPOSIT,
        ),
        (
            "mobile wallet",
            RemittanceType.MOBILE_WALLET,
        ),
        (
            "card-to-card",
            RemittanceType.CARD_TO_CARD,
        ),
        (
            "wallet to wallet",
            RemittanceType.WALLET_TO_WALLET,
        ),
    ],
)
def test_remittance_type_parse(
    raw: str,
    expected: RemittanceType,
) -> None:
    assert RemittanceType.parse(raw) is expected


def test_remittance_type_inventory() -> None:
    assert tuple(
        item.value
        for item in RemittanceType
    ) == (
        "domestic",
        "international",
        "cash_pickup",
        "bank_deposit",
        "mobile_wallet",
        "card_to_card",
        "wallet_to_wallet",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("outbound", RemittanceDirection.OUTBOUND),
        ("send", RemittanceDirection.OUTBOUND),
        ("sent", RemittanceDirection.OUTBOUND),
        ("inbound", RemittanceDirection.INBOUND),
        ("receive", RemittanceDirection.INBOUND),
        ("received", RemittanceDirection.INBOUND),
    ],
)
def test_remittance_direction_parse(
    raw: str,
    expected: RemittanceDirection,
) -> None:
    assert RemittanceDirection.parse(raw) is expected


def test_remittance_direction_inventory() -> None:
    assert tuple(
        item.value
        for item in RemittanceDirection
    ) == (
        "outbound",
        "inbound",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "family support",
            RemittancePurpose.FAMILY_SUPPORT,
        ),
        (
            "family",
            RemittancePurpose.FAMILY_SUPPORT,
        ),
        (
            "education",
            RemittancePurpose.EDUCATION,
        ),
        (
            "education fee",
            RemittancePurpose.EDUCATION,
        ),
        (
            "healthcare",
            RemittancePurpose.HEALTHCARE,
        ),
        (
            "medical",
            RemittancePurpose.HEALTHCARE,
        ),
        (
            "business payment",
            RemittancePurpose.BUSINESS_PAYMENT,
        ),
        (
            "business",
            RemittancePurpose.BUSINESS_PAYMENT,
        ),
        (
            "goods-and-services",
            RemittancePurpose.GOODS_AND_SERVICES,
        ),
        ("savings", RemittancePurpose.SAVINGS),
        ("emergency", RemittancePurpose.EMERGENCY),
        (
            "charitable",
            RemittancePurpose.CHARITABLE,
        ),
        ("other", RemittancePurpose.OTHER),
    ],
)
def test_remittance_purpose_parse(
    raw: str,
    expected: RemittancePurpose,
) -> None:
    assert RemittancePurpose.parse(raw) is expected


def test_remittance_purpose_inventory() -> None:
    assert tuple(
        item.value
        for item in RemittancePurpose
    ) == (
        "family_support",
        "education",
        "healthcare",
        "business_payment",
        "goods_and_services",
        "savings",
        "emergency",
        "charitable",
        "other",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("low", RemittancePriority.LOW),
        ("normal", RemittancePriority.NORMAL),
        ("standard", RemittancePriority.NORMAL),
        ("high", RemittancePriority.HIGH),
        ("urgent", RemittancePriority.URGENT),
        ("express", RemittancePriority.URGENT),
    ],
)
def test_remittance_priority_parse(
    raw: str,
    expected: RemittancePriority,
) -> None:
    assert RemittancePriority.parse(raw) is expected


def test_remittance_priority_inventory() -> None:
    assert tuple(
        item.value
        for item in RemittancePriority
    ) == (
        "low",
        "normal",
        "high",
        "urgent",
    )


@pytest.mark.parametrize(
    "enum_type",
    [
        RemittanceStatus,
        RemittanceType,
        RemittanceDirection,
        RemittancePurpose,
        RemittancePriority,
    ],
)
def test_enum_parse_preserves_instance(
    enum_type: type,
) -> None:
    value = next(iter(enum_type))

    assert enum_type.parse(value) is value


@pytest.mark.parametrize(
    "enum_type",
    [
        RemittanceStatus,
        RemittanceType,
        RemittanceDirection,
        RemittancePurpose,
        RemittancePriority,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        object(),
    ],
)
def test_enums_reject_non_string(
    enum_type: type,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        enum_type.parse(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        RemittanceStatus,
        RemittanceType,
        RemittanceDirection,
        RemittancePurpose,
        RemittancePriority,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "unknown",
        "not-supported",
    ],
)
def test_enums_reject_invalid_string(
    enum_type: type,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse(value)


@pytest.mark.parametrize(
    "value",
    [
        "remittance-001",
        "REM.2026.001",
        "remittance:au-bi:001",
        "remittance_001",
        "r1",
        "x" * 128,
    ],
)
def test_remittance_id_accepts_valid_values(
    value: str,
) -> None:
    remittance_id = RemittanceId.of(value)

    assert remittance_id.value == value
    assert str(remittance_id) == value


def test_remittance_id_preserves_instance() -> None:
    value = RemittanceId.of("remittance-001")

    assert RemittanceId.of(value) is value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "-invalid",
        ".invalid",
        ":invalid",
        "_invalid",
        "invalid value",
        "invalid/value",
        "x" * 129,
    ],
)
def test_remittance_id_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        RemittanceId.of(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        object(),
    ],
)
def test_remittance_id_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        RemittanceId.of(value)


def test_remittance_id_is_orderable() -> None:
    values = sorted(
        [
            RemittanceId.of("remittance-002"),
            RemittanceId.of("remittance-001"),
        ]
    )

    assert [
        item.value
        for item in values
    ] == [
        "remittance-001",
        "remittance-002",
    ]


def test_remittance_id_is_immutable() -> None:
    value = RemittanceId.of("remittance-001")

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "value",
    [
        "reference-001",
        "reference/AU-BI/001",
        "REF:2026:001",
        "customer/remittance_001",
        "r1",
        "x" * 192,
    ],
)
def test_remittance_reference_accepts_valid_values(
    value: str,
) -> None:
    reference = RemittanceReference.of(value)

    assert reference.value == value
    assert str(reference) == value


def test_remittance_reference_preserves_instance() -> None:
    value = RemittanceReference.of(
        "reference/AU-BI/001"
    )

    assert RemittanceReference.of(value) is value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "/invalid",
        "-invalid",
        ".invalid",
        ":invalid",
        "_invalid",
        "invalid reference",
        "x" * 193,
    ],
)
def test_remittance_reference_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        RemittanceReference.of(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        object(),
    ],
)
def test_remittance_reference_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        RemittanceReference.of(value)


def test_remittance_reference_is_orderable() -> None:
    values = sorted(
        [
            RemittanceReference.of("reference-002"),
            RemittanceReference.of("reference-001"),
        ]
    )

    assert [
        item.value
        for item in values
    ] == [
        "reference-001",
        "reference-002",
    ]


def test_remittance_reference_is_immutable() -> None:
    value = RemittanceReference.of(
        "reference-001"
    )

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


def test_metadata_defaults_empty() -> None:
    value = RemittanceMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_metadata_preserves_instance() -> None:
    value = RemittanceMetadata.of(
        {
            "channel": "mobile",
        }
    )

    assert RemittanceMetadata.of(value) is value


def test_metadata_normalizes_keys() -> None:
    value = RemittanceMetadata.of(
        {
            "Channel": "mobile",
            "Pricing Version": "v1",
            "review-state": "complete",
        }
    )

    assert value.values == {
        "channel": "mobile",
        "pricing_version": "v1",
        "review_state": "complete",
    }


def test_metadata_normalizes_nested_mapping() -> None:
    value = RemittanceMetadata.of(
        {
            "review": {
                "Required": True,
                "Risk Level": 2,
            },
        }
    )

    review = value.values["review"]

    assert isinstance(
        review,
        MappingProxyType,
    )
    assert review["required"] is True
    assert review["risk_level"] == 2


def test_metadata_normalizes_lists_to_tuples() -> None:
    value = RemittanceMetadata.of(
        {
            "tags": [
                "consumer",
                "international",
            ],
        }
    )

    assert value.values["tags"] == (
        "consumer",
        "international",
    )


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        1,
        1.5,
        "text",
    ],
)
def test_metadata_accepts_scalar_values(
    value: object,
) -> None:
    metadata = RemittanceMetadata.of(
        {
            "value": value,
        }
    )

    assert metadata.values["value"] == value


@pytest.mark.parametrize(
    "key",
    [
        "access_token",
        "api_key",
        "authorization",
        "bearer",
        "client_secret",
        "credential",
        "cvv",
        "password",
        "pin",
        "private_key",
        "refresh_token",
        "secret",
        "security_code",
        "session_token",
        "token",
        "provider-authorization",
        "api key value",
    ],
)
def test_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        RemittanceMetadata.of(
            {
                key: "sensitive",
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        object(),
        {1, 2},
        b"bytes",
    ],
)
def test_metadata_rejects_non_json_values(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        RemittanceMetadata.of(
            {
                "value": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        [],
        "metadata",
    ],
)
def test_metadata_rejects_non_mapping_root(
    value: object,
) -> None:
    if value is None:
        assert RemittanceMetadata.of(value).values == {}
        return

    with pytest.raises(TypeError):
        RemittanceMetadata.of(value)


def test_metadata_rejects_duplicate_normalized_keys() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate normalized",
    ):
        RemittanceMetadata.of(
            {
                "Review State": "one",
                "review-state": "two",
            }
        )


@pytest.mark.parametrize(
    "key",
    [
        "",
        " ",
        "1invalid",
        "_invalid",
        "invalid!",
        "x" * 65,
    ],
)
def test_metadata_rejects_invalid_keys(
    key: str,
) -> None:
    with pytest.raises(ValueError):
        RemittanceMetadata.of(
            {
                key: "value",
            }
        )


def test_metadata_rejects_excessive_nesting() -> None:
    nested: object = "value"

    for _ in range(10):
        nested = {
            "nested": nested,
        }

    with pytest.raises(
        ValueError,
        match="nesting is too deep",
    ):
        RemittanceMetadata.of(
            {
                "root": nested,
            }
        )


def test_metadata_is_immutable() -> None:
    value = RemittanceMetadata.of(
        {
            "channel": "mobile",
        }
    )

    with pytest.raises(FrozenInstanceError):
        value.values = {}  # type: ignore[misc]

    with pytest.raises(TypeError):
        value.values["channel"] = "web"  # type: ignore[index]


def test_nested_metadata_is_immutable() -> None:
    value = RemittanceMetadata.of(
        {
            "review": {
                "required": True,
            },
        }
    )

    nested = value.values["review"]

    with pytest.raises(TypeError):
        nested["required"] = False  # type: ignore[index]


def test_metadata_canonical_dict_returns_mapping() -> None:
    value = RemittanceMetadata.of(
        {
            "channel": "mobile",
            "tags": ["consumer"],
        }
    )

    payload = value.canonical_dict()

    assert payload is value.values
    assert payload["channel"] == "mobile"
    assert payload["tags"] == ("consumer",)


def test_primitive_module_all_contract() -> None:
    assert remittance.__all__ == [
        "Remittance",
        "RemittanceAmountBreakdown",
        "RemittanceCharge",
        "RemittanceCorridor",
        "RemittanceDirection",
        "RemittanceFee",
        "RemittanceFeeType",
        "RemittanceFundingReference",
        "RemittanceId",
        "RemittanceInstruction",
        "RemittanceInstructionId",
        "RemittanceInstructionMetadata",
        "RemittanceMetadata",
        "RemittancePricingMetadata",
        "RemittancePriority",
        "RemittancePurpose",
        "RemittanceRecipientReference",
        "RemittanceReference",
        "RemittanceStatus",
        "RemittanceType",
    ]


def test_primitive_module_all_sorted() -> None:
    assert remittance.__all__ == sorted(
        remittance.__all__
    )


def test_primitive_module_all_unique() -> None:
    assert len(remittance.__all__) == len(
        set(remittance.__all__)
    )


def test_primitive_module_symbols_exist() -> None:
    for symbol in remittance.__all__:
        assert hasattr(remittance, symbol)


def test_primitive_field_contracts() -> None:
    assert {
        item.name
        for item in fields(RemittanceId)
    } == {"value"}

    assert {
        item.name
        for item in fields(RemittanceReference)
    } == {"value"}

    assert {
        item.name
        for item in fields(RemittanceMetadata)
    } == {"values"}


def test_remittance_aggregate_is_present() -> None:
    assert hasattr(remittance, "Remittance")


def test_completed_remittance_domain_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain

    assert len(remittance.__all__) == 20

    for symbol in remittance.__all__:
        module_value = getattr(remittance, symbol)

        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)
        assert symbol in domain.__all__
        assert symbol in novapay.__all__
        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value

    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(set(novapay.__all__))


def test_primitive_types_have_no_runtime_authority() -> None:
    value_types = (
        RemittanceId,
        RemittanceReference,
        RemittanceMetadata,
    )

    for value_type in value_types:
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "authorize",
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
            "convert",
            "lock_rate",
            "collect",
            "save",
            "persist",
            "repository",
            "database",
        ):
            assert forbidden not in names


def test_primitive_fields_have_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for value_type in (
            RemittanceId,
            RemittanceReference,
            RemittanceMetadata,
        )
        for item in fields(value_type)
    }

    for forbidden in (
        "wallet",
        "ledger",
        "journal",
        "provider_client",
        "settlement_engine",
        "fx_engine",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names
