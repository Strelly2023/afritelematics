from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

import afritech.novapay.domain.settlement_reconciliation as reconciliation
from afritech.novapay.domain.settlement_reconciliation import (
    ReconciliationItem,
    ReconciliationItemStatus,
    ReconciliationMetadata,
    ReconciliationResult,
    ReconciliationStatus,
    ReconciliationSummary,
    SettlementReconciliationId,
)


UTC_TIME = datetime(
    2026,
    8,
    4,
    12,
    0,
    tzinfo=timezone.utc,
)


def create_summary(
    **overrides: object,
) -> ReconciliationSummary:
    values: dict[str, object] = {
        "total_items": 4,
        "pending_items": 0,
        "matched_items": 2,
        "partially_matched_items": 1,
        "unmatched_items": 1,
        "missing_expected_items": 0,
        "missing_observed_items": 0,
        "duplicate_items": 0,
        "conflict_items": 0,
        "excluded_items": 0,
        "review_required_items": 0,
    }

    values.update(overrides)

    return ReconciliationSummary.create(**values)


def create_matched_summary() -> ReconciliationSummary:
    return ReconciliationSummary.create(
        total_items=3,
        matched_items=3,
    )


def create_unmatched_summary() -> ReconciliationSummary:
    return ReconciliationSummary.create(
        total_items=3,
        unmatched_items=3,
    )


def create_partial_summary() -> ReconciliationSummary:
    return ReconciliationSummary.create(
        total_items=3,
        matched_items=1,
        partially_matched_items=1,
        unmatched_items=1,
    )


def create_result(
    **overrides: object,
) -> ReconciliationResult:
    values: dict[str, object] = {
        "reconciliation_id": "recon-result-001",
        "status": "matched",
        "summary": create_matched_summary(),
        "completed_at": UTC_TIME,
        "metadata": {
            "source": "novapay",
        },
    }

    values.update(overrides)

    return ReconciliationResult.create(**values)


def create_item(
    index: int,
    status: object,
) -> ReconciliationItem:
    return ReconciliationItem.create(
        item_id=f"item-{index:03}",
        expected_reference=f"entry-{index:03}",
        status=status,
    )


def test_summary_is_frozen_dataclass() -> None:
    assert is_dataclass(ReconciliationSummary)

    summary = create_summary()

    with pytest.raises(FrozenInstanceError):
        summary.total_items = 5  # type: ignore[misc]


def test_result_is_frozen_dataclass() -> None:
    assert is_dataclass(ReconciliationResult)

    result = create_result()

    with pytest.raises(FrozenInstanceError):
        result.status = (  # type: ignore[misc]
            ReconciliationStatus.CLOSED
        )


def test_summary_field_contract() -> None:
    assert {
        field.name
        for field in fields(ReconciliationSummary)
    } == {
        "total_items",
        "pending_items",
        "matched_items",
        "partially_matched_items",
        "unmatched_items",
        "missing_expected_items",
        "missing_observed_items",
        "duplicate_items",
        "conflict_items",
        "excluded_items",
        "review_required_items",
    }


def test_result_field_contract() -> None:
    assert {
        field.name
        for field in fields(ReconciliationResult)
    } == {
        "reconciliation_id",
        "status",
        "summary",
        "completed_at",
        "metadata",
    }


def test_empty_summary_contract() -> None:
    summary = ReconciliationSummary.empty()

    assert summary.total_items == 0
    assert summary.pending_items == 0
    assert summary.matched_items == 0
    assert summary.discrepancy_items == 0
    assert summary.resolved_items == 0
    assert summary.is_fully_matched is False
    assert summary.has_discrepancies is False
    assert summary.is_complete is True


def test_summary_create_contract() -> None:
    summary = create_summary()

    assert summary.total_items == 4
    assert summary.matched_items == 2
    assert summary.partially_matched_items == 1
    assert summary.unmatched_items == 1
    assert summary.discrepancy_items == 2
    assert summary.resolved_items == 4
    assert summary.is_fully_matched is False
    assert summary.has_discrepancies is True
    assert summary.is_complete is True


@pytest.mark.parametrize(
    "field_name",
    [
        "total_items",
        "pending_items",
        "matched_items",
        "partially_matched_items",
        "unmatched_items",
        "missing_expected_items",
        "missing_observed_items",
        "duplicate_items",
        "conflict_items",
        "excluded_items",
        "review_required_items",
    ],
)
@pytest.mark.parametrize(
    "invalid",
    [
        -1,
        -100,
    ],
)
def test_summary_rejects_negative_counts(
    field_name: str,
    invalid: int,
) -> None:
    values: dict[str, object] = {
        "total_items": 0,
    }

    values[field_name] = invalid

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        ReconciliationSummary.create(**values)


@pytest.mark.parametrize(
    "field_name",
    [
        "total_items",
        "pending_items",
        "matched_items",
        "partially_matched_items",
        "unmatched_items",
        "missing_expected_items",
        "missing_observed_items",
        "duplicate_items",
        "conflict_items",
        "excluded_items",
        "review_required_items",
    ],
)
@pytest.mark.parametrize(
    "invalid",
    [
        True,
        False,
        1.5,
        "1",
        None,
        object(),
    ],
)
def test_summary_rejects_invalid_count_types(
    field_name: str,
    invalid: object,
) -> None:
    values: dict[str, object] = {
        "total_items": 0,
    }

    values[field_name] = invalid

    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        ReconciliationSummary.create(**values)


def test_summary_rejects_classified_total_below_total() -> None:
    with pytest.raises(
        ValueError,
        match="must equal total_items",
    ):
        ReconciliationSummary.create(
            total_items=3,
            matched_items=2,
        )


def test_summary_rejects_classified_total_above_total() -> None:
    with pytest.raises(
        ValueError,
        match="must equal total_items",
    ):
        ReconciliationSummary.create(
            total_items=2,
            matched_items=3,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "status",
    ),
    [
        (
            "pending_items",
            ReconciliationItemStatus.PENDING,
        ),
        (
            "matched_items",
            ReconciliationItemStatus.MATCHED,
        ),
        (
            "partially_matched_items",
            ReconciliationItemStatus.PARTIALLY_MATCHED,
        ),
        (
            "unmatched_items",
            ReconciliationItemStatus.UNMATCHED,
        ),
        (
            "missing_expected_items",
            ReconciliationItemStatus.MISSING_EXPECTED,
        ),
        (
            "missing_observed_items",
            ReconciliationItemStatus.MISSING_OBSERVED,
        ),
        (
            "duplicate_items",
            ReconciliationItemStatus.DUPLICATE,
        ),
        (
            "conflict_items",
            ReconciliationItemStatus.CONFLICT,
        ),
        (
            "excluded_items",
            ReconciliationItemStatus.EXCLUDED,
        ),
        (
            "review_required_items",
            ReconciliationItemStatus.REVIEW_REQUIRED,
        ),
    ],
)
def test_summary_from_items_counts_each_status(
    field_name: str,
    status: ReconciliationItemStatus,
) -> None:
    summary = ReconciliationSummary.from_items(
        [
            create_item(
                1,
                status,
            ),
        ]
    )

    assert summary.total_items == 1
    assert getattr(summary, field_name) == 1


def test_summary_from_items_complete_inventory() -> None:
    statuses = list(ReconciliationItemStatus)

    items = [
        create_item(
            index,
            status,
        )
        for index, status in enumerate(
            statuses,
            start=1,
        )
    ]

    summary = ReconciliationSummary.from_items(items)

    assert summary.total_items == len(statuses)
    assert summary.pending_items == 1
    assert summary.matched_items == 1
    assert summary.partially_matched_items == 1
    assert summary.unmatched_items == 1
    assert summary.missing_expected_items == 1
    assert summary.missing_observed_items == 1
    assert summary.duplicate_items == 1
    assert summary.conflict_items == 1
    assert summary.excluded_items == 1
    assert summary.review_required_items == 1


def test_summary_from_items_accepts_tuple() -> None:
    items = (
        create_item(
            1,
            "matched",
        ),
        create_item(
            2,
            "matched",
        ),
    )

    summary = ReconciliationSummary.from_items(items)

    assert summary.total_items == 2
    assert summary.matched_items == 2


def test_summary_from_items_accepts_generator() -> None:
    items = (
        create_item(
            index,
            "matched",
        )
        for index in range(1, 4)
    )

    summary = ReconciliationSummary.from_items(items)

    assert summary.total_items == 3
    assert summary.matched_items == 3


@pytest.mark.parametrize(
    "invalid",
    [
        "items",
        b"items",
        1,
        None,
        object(),
    ],
)
def test_summary_from_items_rejects_non_iterable(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be iterable",
    ):
        ReconciliationSummary.from_items(invalid)


@pytest.mark.parametrize(
    "invalid_item",
    [
        "item",
        1,
        True,
        None,
        object(),
    ],
)
def test_summary_from_items_rejects_invalid_values(
    invalid_item: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must contain ReconciliationItem values",
    ):
        ReconciliationSummary.from_items(
            [invalid_item]
        )


@pytest.mark.parametrize(
    (
        "summary",
        "expected",
    ),
    [
        (
            ReconciliationSummary.empty(),
            0,
        ),
        (
            ReconciliationSummary.create(
                total_items=1,
                matched_items=1,
            ),
            0,
        ),
        (
            ReconciliationSummary.create(
                total_items=7,
                partially_matched_items=1,
                unmatched_items=1,
                missing_expected_items=1,
                missing_observed_items=1,
                duplicate_items=1,
                conflict_items=1,
                review_required_items=1,
            ),
            7,
        ),
    ],
)
def test_discrepancy_item_calculation(
    summary: ReconciliationSummary,
    expected: int,
) -> None:
    assert summary.discrepancy_items == expected


def test_excluded_items_are_not_discrepancies() -> None:
    summary = ReconciliationSummary.create(
        total_items=2,
        matched_items=1,
        excluded_items=1,
    )

    assert summary.discrepancy_items == 0
    assert summary.has_discrepancies is False


def test_pending_items_are_not_resolved() -> None:
    summary = ReconciliationSummary.create(
        total_items=3,
        matched_items=2,
        pending_items=1,
    )

    assert summary.resolved_items == 2
    assert summary.is_complete is False


def test_excluded_items_are_resolved() -> None:
    summary = ReconciliationSummary.create(
        total_items=2,
        matched_items=1,
        excluded_items=1,
    )

    assert summary.resolved_items == 2
    assert summary.is_complete is True


def test_fully_matched_requires_non_empty_summary() -> None:
    assert (
        ReconciliationSummary.empty().is_fully_matched
        is False
    )


def test_fully_matched_summary_contract() -> None:
    summary = create_matched_summary()

    assert summary.is_fully_matched is True
    assert summary.has_discrepancies is False
    assert summary.is_complete is True


def test_result_factory_normalizes_fields() -> None:
    result = create_result(
        reconciliation_id="  recon-result-001  ",
        status="Matched",
        metadata={
            "Source System": "novapay",
        },
    )

    assert isinstance(
        result.reconciliation_id,
        SettlementReconciliationId,
    )

    assert (
        result.reconciliation_id.value
        == "recon-result-001"
    )

    assert result.status is ReconciliationStatus.MATCHED

    assert isinstance(
        result.metadata,
        ReconciliationMetadata,
    )

    assert result.metadata.canonical_dict() == {
        "source_system": "novapay",
    }


@pytest.mark.parametrize(
    "status",
    [
        ReconciliationStatus.MATCHED,
        ReconciliationStatus.PARTIALLY_MATCHED,
        ReconciliationStatus.UNMATCHED,
        ReconciliationStatus.EXCEPTION,
        ReconciliationStatus.REVIEW_REQUIRED,
        ReconciliationStatus.CLOSED,
        ReconciliationStatus.CANCELED,
        ReconciliationStatus.EXPIRED,
    ],
)
def test_result_supports_result_statuses(
    status: ReconciliationStatus,
) -> None:
    if status is ReconciliationStatus.MATCHED:
        summary = create_matched_summary()
    elif status is ReconciliationStatus.PARTIALLY_MATCHED:
        summary = create_partial_summary()
    elif status is ReconciliationStatus.UNMATCHED:
        summary = create_unmatched_summary()
    else:
        summary = ReconciliationSummary.empty()

    result = create_result(
        status=status,
        summary=summary,
    )

    assert result.status is status


@pytest.mark.parametrize(
    "status",
    [
        ReconciliationStatus.DRAFT,
        ReconciliationStatus.OPEN,
        ReconciliationStatus.COLLECTING,
        ReconciliationStatus.COMPARING,
    ],
)
def test_result_rejects_non_result_statuses(
    status: ReconciliationStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match="classified or terminal status",
    ):
        create_result(
            status=status,
        )


def test_matched_result_requires_fully_matched_summary() -> None:
    with pytest.raises(
        ValueError,
        match="requires a fully matched summary",
    ):
        create_result(
            status="matched",
            summary=create_partial_summary(),
        )


@pytest.mark.parametrize(
    "summary",
    [
        ReconciliationSummary.create(
            total_items=2,
            matched_items=2,
        ),
        ReconciliationSummary.create(
            total_items=2,
            unmatched_items=2,
        ),
        ReconciliationSummary.empty(),
    ],
)
def test_partial_result_rejects_invalid_summary(
    summary: ReconciliationSummary,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires matched and discrepant items",
    ):
        create_result(
            status="partially_matched",
            summary=summary,
        )


def test_partial_result_accepts_mixed_summary() -> None:
    result = create_result(
        status="partially_matched",
        summary=create_partial_summary(),
    )

    assert (
        result.status
        is ReconciliationStatus.PARTIALLY_MATCHED
    )
    assert result.requires_attention is True


@pytest.mark.parametrize(
    "summary",
    [
        ReconciliationSummary.empty(),
        ReconciliationSummary.create(
            total_items=2,
            matched_items=1,
            unmatched_items=1,
        ),
    ],
)
def test_unmatched_result_rejects_invalid_summary(
    summary: ReconciliationSummary,
) -> None:
    with pytest.raises(
        ValueError,
        match="items with no matched items",
    ):
        create_result(
            status="unmatched",
            summary=summary,
        )


def test_unmatched_result_accepts_no_matched_items() -> None:
    result = create_result(
        status="unmatched",
        summary=create_unmatched_summary(),
    )

    assert result.status is ReconciliationStatus.UNMATCHED
    assert result.requires_attention is True


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "summary",
        {},
        [],
        1,
        object(),
    ],
)
def test_result_rejects_invalid_summary_type(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a ReconciliationSummary",
    ):
        create_result(
            summary=invalid,
        )


def test_result_completed_at_normalizes_to_utc() -> None:
    result = create_result(
        completed_at=datetime(
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

    assert result.completed_at == UTC_TIME
    assert result.completed_at.tzinfo is timezone.utc


def test_result_rejects_naive_completed_at() -> None:
    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        create_result(
            completed_at=datetime(
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
        True,
        None,
        object(),
    ],
)
def test_result_rejects_invalid_completed_at_type(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a datetime",
    ):
        create_result(
            completed_at=invalid,
        )


@pytest.mark.parametrize(
    (
        "status",
        "expected",
    ),
    [
        (
            ReconciliationStatus.MATCHED,
            True,
        ),
        (
            ReconciliationStatus.CLOSED,
            True,
        ),
        (
            ReconciliationStatus.PARTIALLY_MATCHED,
            False,
        ),
        (
            ReconciliationStatus.UNMATCHED,
            False,
        ),
        (
            ReconciliationStatus.EXCEPTION,
            False,
        ),
        (
            ReconciliationStatus.REVIEW_REQUIRED,
            False,
        ),
        (
            ReconciliationStatus.CANCELED,
            False,
        ),
        (
            ReconciliationStatus.EXPIRED,
            False,
        ),
    ],
)
def test_result_success_classification(
    status: ReconciliationStatus,
    expected: bool,
) -> None:
    if status is ReconciliationStatus.MATCHED:
        summary = create_matched_summary()
    elif status is ReconciliationStatus.PARTIALLY_MATCHED:
        summary = create_partial_summary()
    elif status is ReconciliationStatus.UNMATCHED:
        summary = create_unmatched_summary()
    else:
        summary = ReconciliationSummary.empty()

    result = create_result(
        status=status,
        summary=summary,
    )

    assert result.is_successful is expected


@pytest.mark.parametrize(
    (
        "status",
        "expected",
    ),
    [
        (
            ReconciliationStatus.MATCHED,
            False,
        ),
        (
            ReconciliationStatus.CLOSED,
            False,
        ),
        (
            ReconciliationStatus.PARTIALLY_MATCHED,
            True,
        ),
        (
            ReconciliationStatus.UNMATCHED,
            True,
        ),
        (
            ReconciliationStatus.EXCEPTION,
            True,
        ),
        (
            ReconciliationStatus.REVIEW_REQUIRED,
            True,
        ),
        (
            ReconciliationStatus.CANCELED,
            False,
        ),
        (
            ReconciliationStatus.EXPIRED,
            False,
        ),
    ],
)
def test_result_attention_classification(
    status: ReconciliationStatus,
    expected: bool,
) -> None:
    if status is ReconciliationStatus.MATCHED:
        summary = create_matched_summary()
    elif status is ReconciliationStatus.PARTIALLY_MATCHED:
        summary = create_partial_summary()
    elif status is ReconciliationStatus.UNMATCHED:
        summary = create_unmatched_summary()
    else:
        summary = ReconciliationSummary.empty()

    result = create_result(
        status=status,
        summary=summary,
    )

    assert result.requires_attention is expected


def test_summary_canonical_dict_contract() -> None:
    summary = create_summary()

    assert summary.canonical_dict() == {
        "total_items": 4,
        "pending_items": 0,
        "matched_items": 2,
        "partially_matched_items": 1,
        "unmatched_items": 1,
        "missing_expected_items": 0,
        "missing_observed_items": 0,
        "duplicate_items": 0,
        "conflict_items": 0,
        "excluded_items": 0,
        "review_required_items": 0,
        "discrepancy_items": 2,
        "resolved_items": 4,
        "is_fully_matched": False,
        "has_discrepancies": True,
        "is_complete": True,
    }


def test_result_canonical_dict_contract() -> None:
    result = create_result()

    assert result.canonical_dict() == {
        "reconciliation_id": "recon-result-001",
        "status": "matched",
        "summary": {
            "total_items": 3,
            "pending_items": 0,
            "matched_items": 3,
            "partially_matched_items": 0,
            "unmatched_items": 0,
            "missing_expected_items": 0,
            "missing_observed_items": 0,
            "duplicate_items": 0,
            "conflict_items": 0,
            "excluded_items": 0,
            "review_required_items": 0,
            "discrepancy_items": 0,
            "resolved_items": 3,
            "is_fully_matched": True,
            "has_discrepancies": False,
            "is_complete": True,
        },
        "completed_at": "2026-08-04T12:00:00+00:00",
        "metadata": {
            "source": "novapay",
        },
        "is_successful": True,
        "requires_attention": False,
    }


def test_summary_serialization_is_deterministic() -> None:
    summary = create_summary()

    assert (
        summary.canonical_dict()
        == summary.canonical_dict()
    )


def test_summary_serialization_returns_fresh_payload() -> None:
    summary = create_summary()

    first = summary.canonical_dict()
    second = summary.canonical_dict()

    assert first is not second


def test_result_serialization_is_deterministic() -> None:
    result = create_result()

    assert (
        result.canonical_dict()
        == result.canonical_dict()
    )


def test_result_serialization_returns_fresh_payloads() -> None:
    result = create_result(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    first = result.canonical_dict()
    second = result.canonical_dict()

    assert first is not second
    assert first["summary"] is not second["summary"]
    assert first["metadata"] is not second["metadata"]

    assert (
        first["metadata"]["nested"]
        is not second["metadata"]["nested"]
    )

    assert (
        first["metadata"]["nested"]["values"]
        is not second["metadata"]["nested"]["values"]
    )


def test_result_serialized_mutation_does_not_leak() -> None:
    result = create_result(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    payload = result.canonical_dict()
    payload["metadata"]["nested"]["values"].append(4)
    payload["summary"]["matched_items"] = 0

    fresh = result.canonical_dict()

    assert fresh["metadata"]["nested"]["values"] == [
        1,
        2,
        3,
    ]
    assert fresh["summary"]["matched_items"] == 3


def test_source_metadata_mutation_does_not_leak() -> None:
    source: dict[str, Any] = {
        "nested": {
            "value": 1,
        },
    }

    result = create_result(
        metadata=source,
    )

    source["nested"]["value"] = 2

    assert result.metadata.canonical_dict() == {
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


@pytest.mark.parametrize(
    "record_type",
    [
        ReconciliationResult,
        ReconciliationSummary,
    ],
)
def test_result_and_summary_have_no_operational_authority(
    record_type: type,
) -> None:
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
        "authorize",
        "reserve",
        "debit",
        "credit",
        "post",
        "submit",
        "send",
        "persist",
        "save",
        "repository",
        "database",
    ):
        assert forbidden not in names


@pytest.mark.parametrize(
    "record_type",
    [
        ReconciliationResult,
        ReconciliationSummary,
    ],
)
def test_result_and_summary_have_no_operational_dependencies(
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
