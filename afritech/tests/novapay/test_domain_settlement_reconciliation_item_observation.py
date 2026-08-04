from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

import afritech.novapay.domain.settlement_reconciliation as reconciliation
from afritech.novapay.domain.settlement_reconciliation import (
    ReconciliationDifference,
    ReconciliationDifferenceId,
    ReconciliationDifferenceType,
    ReconciliationEvidence,
    ReconciliationEvidenceId,
    ReconciliationEvidenceType,
    ReconciliationItem,
    ReconciliationItemId,
    ReconciliationItemStatus,
    ReconciliationMetadata,
    ReconciliationObservation,
    ReconciliationObservationId,
    ReconciliationObservationSource,
)


UTC_TIME = datetime(
    2026,
    8,
    4,
    12,
    0,
    tzinfo=timezone.utc,
)


def create_observation(
    **overrides: object,
) -> ReconciliationObservation:
    values: dict[str, object] = {
        "observation_id": "observation-001",
        "source": "provider",
        "reference": "provider-report-001",
        "observed_at": UTC_TIME,
        "observed_value": "100.00",
        "currency_code": "AUD",
        "metadata": {
            "source": "provider-a",
        },
    }

    values.update(overrides)

    return ReconciliationObservation.create(**values)


def create_difference(
    **overrides: object,
) -> ReconciliationDifference:
    values: dict[str, object] = {
        "difference_id": "difference-001",
        "difference_type": "amount",
        "field_name": "amount",
        "expected_value": "100.00",
        "observed_value": "95.00",
        "detected_at": UTC_TIME,
        "metadata": {
            "severity": "high",
        },
    }

    values.update(overrides)

    return ReconciliationDifference.create(**values)


def create_evidence(
    **overrides: object,
) -> ReconciliationEvidence:
    values: dict[str, object] = {
        "evidence_id": "evidence-001",
        "evidence_type": "hash",
        "reference": "evidence://001",
        "recorded_at": UTC_TIME,
        "digest": "a" * 64,
        "metadata": {
            "format": "json",
        },
    }

    values.update(overrides)

    return ReconciliationEvidence.create(**values)


def create_item(
    **overrides: object,
) -> ReconciliationItem:
    values: dict[str, object] = {
        "item_id": "item-001",
        "expected_reference": "entry-expected-001",
        "observed_reference": "entry-observed-001",
        "status": "partially_matched",
        "observation_ids": [
            "observation-002",
            "observation-001",
        ],
        "difference_ids": [
            "difference-002",
            "difference-001",
        ],
        "evidence_ids": [
            "evidence-002",
            "evidence-001",
        ],
        "metadata": {
            "priority": "high",
        },
    }

    values.update(overrides)

    return ReconciliationItem.create(**values)


@pytest.mark.parametrize(
    "record_type",
    [
        ReconciliationObservation,
        ReconciliationDifference,
        ReconciliationEvidence,
        ReconciliationItem,
    ],
)
def test_record_types_are_frozen_dataclasses(
    record_type: type,
) -> None:
    assert is_dataclass(record_type)


def test_observation_field_contract() -> None:
    assert {
        field.name
        for field in fields(
            ReconciliationObservation
        )
    } == {
        "observation_id",
        "source",
        "reference",
        "observed_at",
        "observed_value",
        "currency_code",
        "metadata",
    }


def test_difference_field_contract() -> None:
    assert {
        field.name
        for field in fields(
            ReconciliationDifference
        )
    } == {
        "difference_id",
        "difference_type",
        "field_name",
        "expected_value",
        "observed_value",
        "detected_at",
        "metadata",
    }


def test_evidence_field_contract() -> None:
    assert {
        field.name
        for field in fields(
            ReconciliationEvidence
        )
    } == {
        "evidence_id",
        "evidence_type",
        "reference",
        "recorded_at",
        "digest",
        "metadata",
    }


def test_item_field_contract() -> None:
    assert {
        field.name
        for field in fields(
            ReconciliationItem
        )
    } == {
        "item_id",
        "status",
        "expected_reference",
        "observed_reference",
        "observation_ids",
        "difference_ids",
        "evidence_ids",
        "metadata",
    }


def test_observation_factory_normalizes_fields() -> None:
    observation = create_observation(
        observation_id="  observation-001  ",
        source="Provider",
        reference="  provider-report-001  ",
        observed_value="  100.00  ",
        currency_code="aud",
        metadata={
            "Source System": "provider-a",
        },
    )

    assert isinstance(
        observation.observation_id,
        ReconciliationObservationId,
    )

    assert (
        observation.observation_id.value
        == "observation-001"
    )

    assert (
        observation.source
        is ReconciliationObservationSource.PROVIDER
    )

    assert observation.reference == "provider-report-001"
    assert observation.observed_value == "100.00"
    assert observation.currency_code == "AUD"

    assert isinstance(
        observation.metadata,
        ReconciliationMetadata,
    )

    assert observation.metadata.canonical_dict() == {
        "source_system": "provider-a",
    }


@pytest.mark.parametrize(
    ("raw_source", "expected"),
    [
        (
            "Settlement Batch",
            ReconciliationObservationSource.SETTLEMENT_BATCH,
        ),
        (
            "settlement-entry",
            ReconciliationObservationSource.SETTLEMENT_ENTRY,
        ),
        (
            "Settlement Instruction",
            ReconciliationObservationSource.SETTLEMENT_INSTRUCTION,
        ),
        (
            "Provider",
            ReconciliationObservationSource.PROVIDER,
        ),
        (
            "Bank",
            ReconciliationObservationSource.BANK,
        ),
        (
            "Ledger",
            ReconciliationObservationSource.LEDGER,
        ),
        (
            "Treasury",
            ReconciliationObservationSource.TREASURY,
        ),
        (
            "Audit Event",
            ReconciliationObservationSource.AUDIT_EVENT,
        ),
        (
            "Operations",
            ReconciliationObservationSource.OPERATIONS,
        ),
        (
            "External Report",
            ReconciliationObservationSource.EXTERNAL_REPORT,
        ),
    ],
)
def test_observation_source_normalization(
    raw_source: str,
    expected: ReconciliationObservationSource,
) -> None:
    observation = create_observation(
        source=raw_source,
    )

    assert observation.source is expected


def test_observation_datetime_normalizes_to_utc() -> None:
    local_timezone = timezone(
        timedelta(hours=10)
    )

    observation = create_observation(
        observed_at=datetime(
            2026,
            8,
            4,
            22,
            0,
            tzinfo=local_timezone,
        )
    )

    assert observation.observed_at == UTC_TIME
    assert observation.observed_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "currency_code",
    [
        "aud",
        "AUD",
        " Aud ",
        "usd",
        "EUR",
    ],
)
def test_observation_currency_normalization(
    currency_code: str,
) -> None:
    observation = create_observation(
        currency_code=currency_code,
    )

    assert observation.currency_code == (
        currency_code.strip().upper()
    )


def test_observation_accepts_none_optional_values() -> None:
    observation = create_observation(
        observed_value=None,
        currency_code=None,
        metadata=None,
    )

    assert observation.observed_value is None
    assert observation.currency_code is None
    assert observation.metadata.canonical_dict() == {}


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
    ],
)
def test_observation_rejects_empty_reference(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_observation(
            reference=invalid,
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
def test_observation_rejects_non_string_reference(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_observation(
            reference=invalid,
        )


def test_observation_rejects_overlength_reference() -> None:
    with pytest.raises(ValueError):
        create_observation(
            reference="x" * 257,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "AU",
        "AUDD",
        "12A",
        "A$D",
    ],
)
def test_observation_rejects_invalid_currency_code(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_observation(
            currency_code=invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        1,
        True,
        object(),
    ],
)
def test_observation_rejects_non_string_currency_code(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_observation(
            currency_code=invalid,
        )


def test_observation_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        create_observation(
            observed_at=datetime(
                2026,
                8,
                4,
                12,
                0,
            )
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "timestamp",
        1,
        None,
        object(),
    ],
)
def test_observation_rejects_non_datetime(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_observation(
            observed_at=invalid,
        )


def test_observation_canonical_dict_contract() -> None:
    observation = create_observation()

    assert observation.canonical_dict() == {
        "observation_id": "observation-001",
        "source": "provider",
        "reference": "provider-report-001",
        "observed_at": "2026-08-04T12:00:00+00:00",
        "observed_value": "100.00",
        "currency_code": "AUD",
        "metadata": {
            "source": "provider-a",
        },
    }


def test_difference_factory_normalizes_fields() -> None:
    difference = create_difference(
        difference_id="  difference-001  ",
        difference_type="Data Quality",
        field_name="  provider amount  ",
        expected_value="  100.00  ",
        observed_value="  95.00  ",
        metadata={
            "Review Level": "high",
        },
    )

    assert isinstance(
        difference.difference_id,
        ReconciliationDifferenceId,
    )

    assert (
        difference.difference_id.value
        == "difference-001"
    )

    assert (
        difference.difference_type
        is ReconciliationDifferenceType.DATA_QUALITY
    )

    assert difference.field_name == "provider amount"
    assert difference.expected_value == "100.00"
    assert difference.observed_value == "95.00"

    assert difference.metadata.canonical_dict() == {
        "review_level": "high",
    }


@pytest.mark.parametrize(
    "difference_type",
    list(ReconciliationDifferenceType),
)
def test_difference_supports_all_types(
    difference_type: ReconciliationDifferenceType,
) -> None:
    difference = create_difference(
        difference_type=difference_type,
    )

    assert difference.difference_type is difference_type


def test_difference_detected_at_normalizes_to_utc() -> None:
    difference = create_difference(
        detected_at=datetime(
            2026,
            8,
            4,
            22,
            0,
            tzinfo=timezone(
                timedelta(hours=10)
            ),
        )
    )

    assert difference.detected_at == UTC_TIME
    assert difference.detected_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    ("expected_value", "observed_value"),
    [
        ("100", None),
        (None, "90"),
        ("100", "90"),
    ],
)
def test_difference_accepts_supported_value_combinations(
    expected_value: str | None,
    observed_value: str | None,
) -> None:
    difference = create_difference(
        expected_value=expected_value,
        observed_value=observed_value,
    )

    assert difference.expected_value == expected_value
    assert difference.observed_value == observed_value


def test_difference_rejects_both_values_missing() -> None:
    with pytest.raises(ValueError):
        create_difference(
            expected_value=None,
            observed_value=None,
        )


def test_difference_rejects_equal_values() -> None:
    with pytest.raises(ValueError):
        create_difference(
            expected_value="same",
            observed_value="same",
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
    ],
)
def test_difference_rejects_empty_field_name(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_difference(
            field_name=invalid,
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
def test_difference_rejects_non_string_field_name(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_difference(
            field_name=invalid,
        )


def test_difference_rejects_overlength_field_name() -> None:
    with pytest.raises(ValueError):
        create_difference(
            field_name="x" * 129,
        )


def test_difference_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        create_difference(
            detected_at=datetime(
                2026,
                8,
                4,
                12,
                0,
            )
        )


def test_difference_canonical_dict_contract() -> None:
    difference = create_difference()

    assert difference.canonical_dict() == {
        "difference_id": "difference-001",
        "difference_type": "amount",
        "field_name": "amount",
        "expected_value": "100.00",
        "observed_value": "95.00",
        "detected_at": "2026-08-04T12:00:00+00:00",
        "metadata": {
            "severity": "high",
        },
    }


def test_evidence_factory_normalizes_fields() -> None:
    evidence = create_evidence(
        evidence_id="  evidence-001  ",
        evidence_type="Provider Report",
        reference="  provider://report/001  ",
        digest=("A" * 64),
        metadata={
            "Evidence Format": "json",
        },
    )

    assert isinstance(
        evidence.evidence_id,
        ReconciliationEvidenceId,
    )

    assert evidence.evidence_id.value == "evidence-001"

    assert (
        evidence.evidence_type
        is ReconciliationEvidenceType.PROVIDER_REPORT
    )

    assert evidence.reference == "provider://report/001"
    assert evidence.digest == "a" * 64

    assert evidence.metadata.canonical_dict() == {
        "evidence_format": "json",
    }


@pytest.mark.parametrize(
    "evidence_type",
    list(ReconciliationEvidenceType),
)
def test_evidence_supports_all_types(
    evidence_type: ReconciliationEvidenceType,
) -> None:
    evidence = create_evidence(
        evidence_type=evidence_type,
    )

    assert evidence.evidence_type is evidence_type


@pytest.mark.parametrize(
    "length",
    [
        32,
        64,
        128,
        256,
    ],
)
def test_evidence_accepts_supported_digest_lengths(
    length: int,
) -> None:
    evidence = create_evidence(
        digest="a" * length,
    )

    assert evidence.digest == "a" * length


def test_evidence_accepts_none_digest() -> None:
    evidence = create_evidence(
        digest=None,
    )

    assert evidence.digest is None


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "abc",
        "a" * 31,
        "a" * 257,
        "z" * 64,
        "g" * 32,
    ],
)
def test_evidence_rejects_invalid_digest(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_evidence(
            digest=invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        1,
        True,
        object(),
    ],
)
def test_evidence_rejects_non_string_digest(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_evidence(
            digest=invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
    ],
)
def test_evidence_rejects_empty_reference(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_evidence(
            reference=invalid,
        )


def test_evidence_rejects_overlength_reference() -> None:
    with pytest.raises(ValueError):
        create_evidence(
            reference="x" * 513,
        )


def test_evidence_recorded_at_normalizes_to_utc() -> None:
    evidence = create_evidence(
        recorded_at=datetime(
            2026,
            8,
            4,
            22,
            0,
            tzinfo=timezone(
                timedelta(hours=10)
            ),
        )
    )

    assert evidence.recorded_at == UTC_TIME
    assert evidence.recorded_at.tzinfo is timezone.utc


def test_evidence_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        create_evidence(
            recorded_at=datetime(
                2026,
                8,
                4,
                12,
                0,
            )
        )


def test_evidence_canonical_dict_contract() -> None:
    evidence = create_evidence()

    assert evidence.canonical_dict() == {
        "evidence_id": "evidence-001",
        "evidence_type": "hash",
        "reference": "evidence://001",
        "recorded_at": "2026-08-04T12:00:00+00:00",
        "digest": "a" * 64,
        "metadata": {
            "format": "json",
        },
    }


def test_item_factory_normalizes_fields() -> None:
    item = create_item(
        item_id="  item-001  ",
        status="Review Required",
        expected_reference="  expected-entry-001  ",
        observed_reference="  observed-entry-001  ",
        metadata={
            "Review Priority": "high",
        },
    )

    assert isinstance(
        item.item_id,
        ReconciliationItemId,
    )

    assert item.item_id.value == "item-001"

    assert (
        item.status
        is ReconciliationItemStatus.REVIEW_REQUIRED
    )

    assert item.expected_reference == "expected-entry-001"
    assert item.observed_reference == "observed-entry-001"

    assert item.metadata.canonical_dict() == {
        "review_priority": "high",
    }


@pytest.mark.parametrize(
    "status",
    list(ReconciliationItemStatus),
)
def test_item_supports_all_statuses(
    status: ReconciliationItemStatus,
) -> None:
    item = create_item(
        status=status,
    )

    assert item.status is status


def test_item_defaults_to_pending_status() -> None:
    item = ReconciliationItem.create(
        item_id="item-001",
        expected_reference="entry-001",
    )

    assert item.status is ReconciliationItemStatus.PENDING


def test_item_accepts_none_observed_reference() -> None:
    item = create_item(
        observed_reference=None,
    )

    assert item.observed_reference is None


def test_item_normalizes_identifier_collections() -> None:
    item = create_item(
        observation_ids=[
            "observation-003",
            "observation-001",
            "observation-002",
        ],
        difference_ids=[
            "difference-003",
            "difference-001",
            "difference-002",
        ],
        evidence_ids=[
            "evidence-003",
            "evidence-001",
            "evidence-002",
        ],
    )

    assert item.observation_ids == (
        ReconciliationObservationId.of(
            "observation-001"
        ),
        ReconciliationObservationId.of(
            "observation-002"
        ),
        ReconciliationObservationId.of(
            "observation-003"
        ),
    )

    assert item.difference_ids == (
        ReconciliationDifferenceId.of(
            "difference-001"
        ),
        ReconciliationDifferenceId.of(
            "difference-002"
        ),
        ReconciliationDifferenceId.of(
            "difference-003"
        ),
    )

    assert item.evidence_ids == (
        ReconciliationEvidenceId.of(
            "evidence-001"
        ),
        ReconciliationEvidenceId.of(
            "evidence-002"
        ),
        ReconciliationEvidenceId.of(
            "evidence-003"
        ),
    )


def test_item_accepts_identifier_objects() -> None:
    observation_id = ReconciliationObservationId.of(
        "observation-001"
    )
    difference_id = ReconciliationDifferenceId.of(
        "difference-001"
    )
    evidence_id = ReconciliationEvidenceId.of(
        "evidence-001"
    )

    item = create_item(
        observation_ids=[observation_id],
        difference_ids=[difference_id],
        evidence_ids=[evidence_id],
    )

    assert item.observation_ids == (
        observation_id,
    )
    assert item.difference_ids == (
        difference_id,
    )
    assert item.evidence_ids == (
        evidence_id,
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "observation_ids",
        "difference_ids",
        "evidence_ids",
    ],
)
def test_item_rejects_duplicate_identifiers(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        create_item(
            **{
                field_name: [
                    "duplicate-001",
                    "duplicate-001",
                ],
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "observation_ids",
        "difference_ids",
        "evidence_ids",
    ],
)
@pytest.mark.parametrize(
    "invalid",
    [
        "identifier",
        b"identifier",
        1,
        None,
        object(),
    ],
)
def test_item_rejects_non_iterable_identifier_collections(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_item(
            **{
                field_name: invalid,
            }
        )


def test_item_empty_collection_flags_are_false() -> None:
    item = ReconciliationItem.create(
        item_id="item-001",
        expected_reference="entry-001",
    )

    assert item.has_observations is False
    assert item.has_differences is False
    assert item.has_evidence is False


def test_item_populated_collection_flags_are_true() -> None:
    item = create_item()

    assert item.has_observations is True
    assert item.has_differences is True
    assert item.has_evidence is True


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "\t",
    ],
)
def test_item_rejects_empty_expected_reference(
    invalid: str,
) -> None:
    with pytest.raises(ValueError):
        create_item(
            expected_reference=invalid,
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
def test_item_rejects_non_string_expected_reference(
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        create_item(
            expected_reference=invalid,
        )


def test_item_rejects_overlength_expected_reference() -> None:
    with pytest.raises(ValueError):
        create_item(
            expected_reference="x" * 257,
        )


def test_item_canonical_dict_contract() -> None:
    item = create_item()

    assert item.canonical_dict() == {
        "item_id": "item-001",
        "status": "partially_matched",
        "expected_reference": "entry-expected-001",
        "observed_reference": "entry-observed-001",
        "observation_ids": [
            "observation-001",
            "observation-002",
        ],
        "difference_ids": [
            "difference-001",
            "difference-002",
        ],
        "evidence_ids": [
            "evidence-001",
            "evidence-002",
        ],
        "metadata": {
            "priority": "high",
        },
    }


@pytest.mark.parametrize(
    "factory",
    [
        create_observation,
        create_difference,
        create_evidence,
        create_item,
    ],
)
def test_records_are_immutable(
    factory: Any,
) -> None:
    record = factory()

    with pytest.raises(FrozenInstanceError):
        record.metadata = None  # type: ignore[misc]


@pytest.mark.parametrize(
    "factory",
    [
        create_observation,
        create_difference,
        create_evidence,
        create_item,
    ],
)
def test_record_serialization_is_deterministic(
    factory: Any,
) -> None:
    record = factory()

    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first == second


@pytest.mark.parametrize(
    "factory",
    [
        create_observation,
        create_difference,
        create_evidence,
        create_item,
    ],
)
def test_record_serialization_returns_fresh_payload(
    factory: Any,
) -> None:
    record = factory(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first is not second
    assert first["metadata"] is not second["metadata"]

    assert (
        first["metadata"]["nested"]
        is not second["metadata"]["nested"]
    )

    assert (
        first["metadata"]["nested"]["values"]
        is not second["metadata"]["nested"]["values"]
    )


@pytest.mark.parametrize(
    "factory",
    [
        create_observation,
        create_difference,
        create_evidence,
        create_item,
    ],
)
def test_serialized_mutation_does_not_leak(
    factory: Any,
) -> None:
    record = factory(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    payload = record.canonical_dict()
    payload["metadata"]["nested"]["values"].append(4)

    assert record.canonical_dict()[
        "metadata"
    ]["nested"]["values"] == [1, 2, 3]


@pytest.mark.parametrize(
    "factory",
    [
        create_observation,
        create_difference,
        create_evidence,
        create_item,
    ],
)
def test_source_metadata_mutation_does_not_leak(
    factory: Any,
) -> None:
    source: dict[str, Any] = {
        "nested": {
            "value": 1,
        },
    }

    record = factory(
        metadata=source,
    )

    source["nested"]["value"] = 2

    assert record.metadata.canonical_dict() == {
        "nested": {
            "value": 1,
        },
    }


def test_reconciliation_domain_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    import afritech.novapay.domain.settlement_reconciliation as module

    for symbol in module.__all__:
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)
        assert symbol in domain.__all__
        assert symbol in novapay.__all__

        assert getattr(domain, symbol) is getattr(
            module,
            symbol,
        )
        assert getattr(novapay, symbol) is getattr(
            module,
            symbol,
        )


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


def test_lifecycle_foundation_is_present() -> None:
    lifecycle_methods = (
        "open",
        "start_collecting",
        "start_comparing",
        "mark_matched",
        "mark_partially_matched",
        "mark_unmatched",
        "mark_exception",
        "require_review",
        "close",
        "cancel",
        "expire",
        "update_metadata",
    )

    for method_name in lifecycle_methods:
        assert hasattr(
            reconciliation.SettlementReconciliation,
            method_name,
        )


def test_lifecycle_execution_authority_remains_absent() -> None:
    for method_name in (
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
        assert not hasattr(
            reconciliation.SettlementReconciliation,
            method_name,
        )


@pytest.mark.parametrize(
    "record_type",
    [
        ReconciliationObservation,
        ReconciliationDifference,
        ReconciliationEvidence,
        ReconciliationItem,
    ],
)
def test_records_have_no_operational_authority(
    record_type: type,
) -> None:
    names = {
        name
        for name in dir(record_type)
        if not name.startswith("__")
    }

    for forbidden in (
        "authorize",
        "reserve",
        "debit",
        "credit",
        "post",
        "execute",
        "settle",
        "compare",
        "match",
        "reconcile",
        "resolve",
        "adjust",
        "submit",
        "send",
        "collect",
        "save",
        "persist",
        "repository",
        "database",
    ):
        assert forbidden not in names


@pytest.mark.parametrize(
    "record_type",
    [
        ReconciliationObservation,
        ReconciliationDifference,
        ReconciliationEvidence,
        ReconciliationItem,
    ],
)
def test_records_have_no_operational_dependencies(
    record_type: type,
) -> None:
    field_names = {
        field.name
        for field in fields(record_type)
    }

    for forbidden in (
        "wallet",
        "wallet_repository",
        "ledger",
        "journal",
        "provider_client",
        "settlement_engine",
        "reconciliation_engine",
        "repository",
        "database",
        "credentials",
    ):
        assert forbidden not in field_names
