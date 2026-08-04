from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

import pytest

import afritech.novapay.domain.settlement_reconciliation as reconciliation
from afritech.novapay.domain.settlement_reconciliation import (
    ReconciliationDifferenceId,
    ReconciliationDifferenceType,
    ReconciliationEvidenceId,
    ReconciliationEvidenceType,
    ReconciliationItemId,
    ReconciliationItemStatus,
    ReconciliationMetadata,
    ReconciliationObservationId,
    ReconciliationObservationSource,
    ReconciliationStatus,
    ReconciliationType,
    SettlementReconciliationId,
)


IDENTIFIER_TYPES = (
    SettlementReconciliationId,
    ReconciliationItemId,
    ReconciliationObservationId,
    ReconciliationDifferenceId,
    ReconciliationEvidenceId,
)

ENUM_TYPES = (
    ReconciliationType,
    ReconciliationStatus,
    ReconciliationItemStatus,
    ReconciliationObservationSource,
    ReconciliationDifferenceType,
    ReconciliationEvidenceType,
)

EXPECTED_ALL = [
    "ReconciliationDifference",
    "ReconciliationDifferenceId",
    "ReconciliationDifferenceType",
    "ReconciliationEvidence",
    "ReconciliationEvidenceId",
    "ReconciliationEvidenceType",
    "ReconciliationItem",
    "ReconciliationItemId",
    "ReconciliationItemStatus",
    "ReconciliationMetadata",
    "ReconciliationObservation",
    "ReconciliationObservationId",
    "ReconciliationObservationSource",
    "ReconciliationResult",
    "ReconciliationStatus",
    "ReconciliationSummary",
    "ReconciliationType",
    "SettlementReconciliation",
    "SettlementReconciliationId",
]


def test_module_public_inventory() -> None:
    assert reconciliation.__all__ == EXPECTED_ALL
    assert reconciliation.__all__ == sorted(
        reconciliation.__all__
    )
    assert len(reconciliation.__all__) == 19
    assert len(reconciliation.__all__) == len(
        set(reconciliation.__all__)
    )

    for symbol in reconciliation.__all__:
        assert hasattr(reconciliation, symbol)


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
def test_identifier_types_are_frozen_dataclasses(
    value_type: type,
) -> None:
    assert is_dataclass(value_type)
    assert {
        field.name
        for field in fields(value_type)
    } == {"value"}

    value = value_type.of("identifier-001")

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
def test_identifier_normalization(
    value_type: type,
) -> None:
    value = value_type.of(
        "  identifier-001  "
    )

    assert value.value == "identifier-001"
    assert str(value) == "identifier-001"


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
def test_identifier_idempotence(
    value_type: type,
) -> None:
    value = value_type.of(
        "identifier-001"
    )

    assert value_type.of(value) is value


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "ABC",
        "abc-123",
        "abc_123",
        "abc.123",
        "abc/123",
        "abc:123",
        "abc-123_456.789/path:segment",
    ],
)
def test_identifier_accepts_supported_characters(
    value_type: type,
    value: str,
) -> None:
    assert value_type.of(value).value == value


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
        "\n",
        "identifier value",
        "identifier?",
        "identifier#",
        "identifier@",
        "identifier%",
        None,
        1,
        True,
        object(),
    ],
)
def test_identifier_rejects_invalid_values(
    value_type: type,
    invalid: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        value_type.of(invalid)


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
def test_identifier_rejects_overlength_values(
    value_type: type,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 160 characters",
    ):
        value_type.of("a" * 161)


@pytest.mark.parametrize(
    "value_type",
    IDENTIFIER_TYPES,
)
def test_identifier_supports_ordering(
    value_type: type,
) -> None:
    first = value_type.of("identifier-001")
    second = value_type.of("identifier-002")

    assert first < second
    assert sorted([second, first]) == [
        first,
        second,
    ]


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
def test_enum_types_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
def test_enum_parse_is_idempotent(
    enum_type: type,
) -> None:
    for member in enum_type:
        assert enum_type.parse(member) is member
        assert enum_type.parse(
            member.value
        ) is member


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
def test_enum_canonical_value(
    enum_type: type,
) -> None:
    for member in enum_type:
        assert member.canonical_value() == member.value


@pytest.mark.parametrize(
    ("enum_type", "raw_value", "expected"),
    [
        (
            ReconciliationType,
            "Settlement Batch",
            ReconciliationType.SETTLEMENT_BATCH,
        ),
        (
            ReconciliationType,
            "provider-report",
            ReconciliationType.PROVIDER_REPORT,
        ),
        (
            ReconciliationStatus,
            "PARTIALLY MATCHED",
            ReconciliationStatus.PARTIALLY_MATCHED,
        ),
        (
            ReconciliationStatus,
            "review-required",
            ReconciliationStatus.REVIEW_REQUIRED,
        ),
        (
            ReconciliationItemStatus,
            "Missing Expected",
            ReconciliationItemStatus.MISSING_EXPECTED,
        ),
        (
            ReconciliationItemStatus,
            "missing-observed",
            ReconciliationItemStatus.MISSING_OBSERVED,
        ),
        (
            ReconciliationObservationSource,
            "Audit Event",
            ReconciliationObservationSource.AUDIT_EVENT,
        ),
        (
            ReconciliationObservationSource,
            "external-report",
            ReconciliationObservationSource.EXTERNAL_REPORT,
        ),
        (
            ReconciliationDifferenceType,
            "Data Quality",
            ReconciliationDifferenceType.DATA_QUALITY,
        ),
        (
            ReconciliationDifferenceType,
            "missing observed",
            ReconciliationDifferenceType.MISSING_OBSERVED,
        ),
        (
            ReconciliationEvidenceType,
            "Ledger Checkpoint",
            ReconciliationEvidenceType.LEDGER_CHECKPOINT,
        ),
        (
            ReconciliationEvidenceType,
            "external-reference",
            ReconciliationEvidenceType.EXTERNAL_REFERENCE,
        ),
    ],
)
def test_enum_normalized_parsing(
    enum_type: type,
    raw_value: str,
    expected: Enum,
) -> None:
    assert enum_type.parse(
        raw_value
    ) is expected


@pytest.mark.parametrize(
    "enum_type",
    ENUM_TYPES,
)
@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
        "not-supported",
        "unknown value",
        None,
        1,
        True,
        object(),
    ],
)
def test_enum_rejects_invalid_values(
    enum_type: type,
    invalid: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        enum_type.parse(invalid)


def test_reconciliation_type_members() -> None:
    assert {
        member.value
        for member in ReconciliationType
    } == {
        "settlement_batch",
        "settlement_entry",
        "settlement_instruction",
        "provider_report",
        "bank_statement",
        "ledger_checkpoint",
        "treasury_position",
        "operational_report",
    }


def test_reconciliation_status_members() -> None:
    assert {
        member.value
        for member in ReconciliationStatus
    } == {
        "draft",
        "open",
        "collecting",
        "comparing",
        "matched",
        "partially_matched",
        "unmatched",
        "exception",
        "review_required",
        "closed",
        "canceled",
        "expired",
    }


def test_reconciliation_item_status_members() -> None:
    assert {
        member.value
        for member in ReconciliationItemStatus
    } == {
        "pending",
        "matched",
        "partially_matched",
        "unmatched",
        "missing_expected",
        "missing_observed",
        "duplicate",
        "conflict",
        "excluded",
        "review_required",
    }


def test_observation_source_members() -> None:
    assert {
        member.value
        for member in ReconciliationObservationSource
    } == {
        "settlement_batch",
        "settlement_entry",
        "settlement_instruction",
        "provider",
        "bank",
        "ledger",
        "treasury",
        "audit_event",
        "operations",
        "external_report",
    }


def test_difference_type_members() -> None:
    assert {
        member.value
        for member in ReconciliationDifferenceType
    } == {
        "amount",
        "currency",
        "status",
        "count",
        "reference",
        "timestamp",
        "participant",
        "missing_expected",
        "missing_observed",
        "duplicate",
        "data_quality",
        "other",
    }


def test_evidence_type_members() -> None:
    assert {
        member.value
        for member in ReconciliationEvidenceType
    } == {
        "settlement_result",
        "settlement_summary",
        "provider_report",
        "bank_statement",
        "ledger_checkpoint",
        "treasury_report",
        "audit_event",
        "receipt",
        "hash",
        "signature",
        "external_reference",
        "operational_note",
    }


def test_metadata_is_frozen_dataclass() -> None:
    assert is_dataclass(
        ReconciliationMetadata
    )

    assert {
        field.name
        for field in fields(
            ReconciliationMetadata
        )
    } == {"values"}

    metadata = ReconciliationMetadata.empty()

    with pytest.raises(FrozenInstanceError):
        metadata.values = {}  # type: ignore[misc]


def test_metadata_none_creates_empty_value() -> None:
    metadata = ReconciliationMetadata.of(None)

    assert len(metadata) == 0
    assert bool(metadata) is False
    assert metadata.canonical_dict() == {}


def test_metadata_of_is_idempotent() -> None:
    metadata = ReconciliationMetadata.of(
        {"source": "novapay"}
    )

    assert ReconciliationMetadata.of(
        metadata
    ) is metadata


def test_metadata_normalizes_keys() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "Source System": "novapay",
            "Provider-Reference": "provider-001",
            "Batch.Version": 2,
        }
    )

    assert metadata.canonical_dict() == {
        "batch_version": 2,
        "provider_reference": "provider-001",
        "source_system": "novapay",
    }


def test_metadata_orders_keys_deterministically() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "zeta": 1,
            "alpha": 2,
            "middle": 3,
        }
    )

    assert list(
        metadata.values.keys()
    ) == [
        "alpha",
        "middle",
        "zeta",
    ]


def test_metadata_deeply_freezes_nested_values() -> None:
    source: dict[str, Any] = {
        "nested": {
            "sequence": [
                1,
                2,
                {
                    "status": ReconciliationStatus.OPEN,
                },
            ],
        },
    }

    metadata = ReconciliationMetadata.of(source)

    assert isinstance(
        metadata.values,
        MappingProxyType,
    )

    nested = metadata.values["nested"]

    assert isinstance(nested, MappingProxyType)
    assert isinstance(
        nested["sequence"],
        tuple,
    )

    nested_record = nested["sequence"][2]

    assert isinstance(
        nested_record,
        MappingProxyType,
    )

    assert nested_record["status"] == "open"


def test_metadata_isolated_from_source_mutation() -> None:
    source: dict[str, Any] = {
        "source": "novapay",
        "nested": {
            "value": 1,
        },
    }

    metadata = ReconciliationMetadata.of(source)

    source["source"] = "changed"
    source["nested"]["value"] = 2

    assert metadata.canonical_dict() == {
        "nested": {
            "value": 1,
        },
        "source": "novapay",
    }


def test_metadata_top_level_mapping_is_immutable() -> None:
    metadata = ReconciliationMetadata.of(
        {"source": "novapay"}
    )

    with pytest.raises(TypeError):
        metadata.values["source"] = "changed"  # type: ignore[index]


def test_metadata_nested_mapping_is_immutable() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "nested": {
                "source": "novapay",
            }
        }
    )

    nested = metadata.values["nested"]

    assert isinstance(
        nested,
        MappingProxyType,
    )

    with pytest.raises(TypeError):
        nested["source"] = "changed"  # type: ignore[index]


def test_metadata_canonical_dict_is_fresh() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "nested": {
                "values": [
                    1,
                    2,
                    3,
                ]
            }
        }
    )

    first = metadata.canonical_dict()
    second = metadata.canonical_dict()

    assert first == second
    assert first is not second
    assert first["nested"] is not second["nested"]
    assert (
        first["nested"]["values"]
        is not second["nested"]["values"]
    )


def test_metadata_serialized_mutation_does_not_leak() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "nested": {
                "values": [
                    1,
                    2,
                    3,
                ]
            }
        }
    )

    payload = metadata.canonical_dict()

    payload["nested"]["values"].append(4)

    assert metadata.canonical_dict() == {
        "nested": {
            "values": [
                1,
                2,
                3,
            ]
        }
    }


@pytest.mark.parametrize(
    "invalid",
    [
        "metadata",
        1,
        True,
        [],
        (),
        object(),
    ],
)
def test_metadata_rejects_invalid_root_types(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        ReconciliationMetadata.of(invalid)


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "password",
        "private_key",
        "api_key",
        "token",
        "secret",
        "credential",
        "credentials",
        "pin",
        "cvv",
        "security_code",
        "card_number",
        "access_token",
    ],
)
def test_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        ReconciliationMetadata.of(
            {
                key: "sensitive",
            }
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        object(),
        complex(1, 2),
        b"bytes",
    ],
)
def test_metadata_rejects_unsupported_values(
    invalid_value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="unsupported reconciliation metadata value type",
    ):
        ReconciliationMetadata.of(
            {
                "value": invalid_value,
            }
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        {"a", "b"},
        frozenset({"a", "b"}),
    ],
)
def test_metadata_rejects_sets(
    invalid_value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="sets are not supported",
    ):
        ReconciliationMetadata.of(
            {
                "value": invalid_value,
            }
        )


def test_metadata_rejects_duplicate_normalized_keys() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate normalized key",
    ):
        ReconciliationMetadata.of(
            {
                "Source System": "one",
                "source-system": "two",
            }
        )


def test_metadata_rejects_overlength_string() -> None:
    with pytest.raises(
        ValueError,
        match="metadata string exceeds 4096 characters",
    ):
        ReconciliationMetadata.of(
            {
                "value": "x" * 4097,
            }
        )


def test_metadata_rejects_oversized_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="mapping exceeds 128 items",
    ):
        ReconciliationMetadata.of(
            {
                f"key_{index}": index
                for index in range(129)
            }
        )


def test_metadata_rejects_oversized_sequence() -> None:
    with pytest.raises(
        ValueError,
        match="sequence exceeds 128 items",
    ):
        ReconciliationMetadata.of(
            {
                "values": list(range(129)),
            }
        )


def test_metadata_rejects_excessive_depth() -> None:
    nested: dict[str, object] = {
        "value": "leaf",
    }

    for _ in range(9):
        nested = {
            "nested": nested,
        }

    with pytest.raises(
        ValueError,
        match="exceeds maximum depth",
    ):
        ReconciliationMetadata.of(nested)


def test_metadata_enum_values_serialize_as_strings() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "status": ReconciliationStatus.OPEN,
            "type": ReconciliationType.SETTLEMENT_BATCH,
        }
    )

    assert metadata.canonical_dict() == {
        "status": "open",
        "type": "settlement_batch",
    }


def test_metadata_accepts_supported_scalars() -> None:
    metadata = ReconciliationMetadata.of(
        {
            "none": None,
            "boolean": True,
            "integer": 1,
            "float": 1.5,
            "string": "value",
        }
    )

    assert metadata.canonical_dict() == {
        "boolean": True,
        "float": 1.5,
        "integer": 1,
        "none": None,
        "string": "value",
    }


def test_primitives_are_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain

    for symbol in reconciliation.__all__:
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)

        assert symbol in domain.__all__
        assert symbol in novapay.__all__

        canonical = getattr(
            reconciliation,
            symbol,
        )

        assert getattr(domain, symbol) is canonical
        assert getattr(novapay, symbol) is canonical


def test_primitives_have_no_operational_authority() -> None:
    value_types = (
        *IDENTIFIER_TYPES,
        *ENUM_TYPES,
        ReconciliationMetadata,
    )

    forbidden = (
        "authorize",
        "reserve",
        "reserve_funds",
        "debit",
        "credit",
        "post",
        "post_entry",
        "execute",
        "settle",
        "reconcile",
        "resolve",
        "adjust",
        "submit",
        "submit_to_provider",
        "send",
        "select_provider",
        "collect",
        "collect_fee",
        "save",
        "persist",
        "repository",
        "database",
    )

    for value_type in value_types:
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for method_name in forbidden:
            assert method_name not in names


def test_aggregate_foundation_is_present() -> None:
    assert hasattr(
        reconciliation,
        "SettlementReconciliation",
    )
    assert (
        "SettlementReconciliation"
        in reconciliation.__all__
    )

    aggregate_type = (
        reconciliation.SettlementReconciliation
    )

    assert aggregate_type.__module__ == (
        "afritech.novapay.domain."
        "settlement_reconciliation"
    )


def test_reconciliation_record_foundation_is_present() -> None:
    for symbol in (
        "ReconciliationItem",
        "ReconciliationObservation",
        "ReconciliationDifference",
        "ReconciliationEvidence",
    ):
        assert hasattr(reconciliation, symbol)
        assert symbol in reconciliation.__all__


def test_result_and_summary_foundation_is_present() -> None:
    for symbol in (
        "ReconciliationResult",
        "ReconciliationSummary",
    ):
        assert hasattr(reconciliation, symbol)
        assert symbol in reconciliation.__all__


def test_result_and_summary_execution_authority_remains_absent() -> None:
    for record_type in (
        reconciliation.ReconciliationResult,
        reconciliation.ReconciliationSummary,
    ):
        names = {
            name
            for name in dir(record_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "compare",
            "match",
            "reconcile",
            "resolve",
            "execute",
            "settle",
            "persist",
            "save",
            "submit",
            "post",
            "debit",
            "credit",
        ):
            assert forbidden not in names
