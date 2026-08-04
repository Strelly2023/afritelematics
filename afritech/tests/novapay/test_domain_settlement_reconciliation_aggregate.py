from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

import afritech.novapay.domain.settlement_reconciliation as reconciliation
from afritech.novapay.domain.settlement_batch import (
    SettlementBatchId,
)
from afritech.novapay.domain.settlement_reconciliation import (
    ReconciliationMetadata,
    ReconciliationStatus,
    ReconciliationType,
    SettlementReconciliation,
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


def create_reconciliation(
    **overrides: object,
) -> SettlementReconciliation:
    values: dict[str, object] = {
        "reconciliation_id": "recon-001",
        "reconciliation_type": "settlement_batch",
        "settlement_batch_id": "batch-001",
        "expected_entry_count": 4,
        "created_at": UTC_TIME,
        "metadata": {
            "source": "novapay",
        },
    }

    values.update(overrides)

    return SettlementReconciliation.create(**values)


def construct_reconciliation(
    **overrides: object,
) -> SettlementReconciliation:
    values: dict[str, object] = {
        "reconciliation_id": "recon-001",
        "reconciliation_type": "settlement_batch",
        "status": "draft",
        "settlement_batch_id": "batch-001",
        "expected_entry_count": 4,
        "created_at": UTC_TIME,
        "updated_at": UTC_TIME,
        "version": 1,
        "metadata": {
            "source": "novapay",
        },
    }

    values.update(overrides)

    return SettlementReconciliation(**values)


def test_aggregate_is_frozen_dataclass() -> None:
    assert is_dataclass(
        SettlementReconciliation
    )

    aggregate = create_reconciliation()

    with pytest.raises(FrozenInstanceError):
        aggregate.version = 2  # type: ignore[misc]


def test_aggregate_field_contract() -> None:
    assert {
        field.name
        for field in fields(
            SettlementReconciliation
        )
    } == {
        "reconciliation_id",
        "reconciliation_type",
        "status",
        "settlement_batch_id",
        "expected_entry_count",
        "created_at",
        "updated_at",
        "version",
        "metadata",
    }


def test_factory_normalizes_identifiers() -> None:
    aggregate = create_reconciliation(
        reconciliation_id="  recon-001  ",
        settlement_batch_id="  batch-001  ",
    )

    assert isinstance(
        aggregate.reconciliation_id,
        SettlementReconciliationId,
    )
    assert isinstance(
        aggregate.settlement_batch_id,
        SettlementBatchId,
    )

    assert (
        aggregate.reconciliation_id.value
        == "recon-001"
    )
    assert (
        aggregate.settlement_batch_id.value
        == "batch-001"
    )


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (
            "Settlement Batch",
            ReconciliationType.SETTLEMENT_BATCH,
        ),
        (
            "settlement-entry",
            ReconciliationType.SETTLEMENT_ENTRY,
        ),
        (
            "SETTLEMENT INSTRUCTION",
            ReconciliationType.SETTLEMENT_INSTRUCTION,
        ),
        (
            "Provider Report",
            ReconciliationType.PROVIDER_REPORT,
        ),
        (
            "bank-statement",
            ReconciliationType.BANK_STATEMENT,
        ),
        (
            "Ledger Checkpoint",
            ReconciliationType.LEDGER_CHECKPOINT,
        ),
        (
            "treasury-position",
            ReconciliationType.TREASURY_POSITION,
        ),
        (
            "Operational Report",
            ReconciliationType.OPERATIONAL_REPORT,
        ),
    ],
)
def test_factory_normalizes_reconciliation_type(
    raw_value: str,
    expected: ReconciliationType,
) -> None:
    aggregate = create_reconciliation(
        reconciliation_type=raw_value,
    )

    assert (
        aggregate.reconciliation_type
        is expected
    )


def test_factory_sets_draft_status() -> None:
    aggregate = create_reconciliation()

    assert (
        aggregate.status
        is ReconciliationStatus.DRAFT
    )
    assert aggregate.is_draft is True


def test_factory_sets_version_one() -> None:
    aggregate = create_reconciliation()

    assert aggregate.version == 1


def test_factory_sets_matching_timestamps() -> None:
    aggregate = create_reconciliation()

    assert (
        aggregate.created_at
        == aggregate.updated_at
    )


def test_factory_normalizes_datetime_to_utc() -> None:
    melbourne = timezone(
        timedelta(hours=10)
    )

    aggregate = create_reconciliation(
        created_at=datetime(
            2026,
            8,
            4,
            22,
            0,
            tzinfo=melbourne,
        )
    )

    assert aggregate.created_at == UTC_TIME
    assert aggregate.updated_at == UTC_TIME
    assert aggregate.created_at.tzinfo is timezone.utc
    assert aggregate.updated_at.tzinfo is timezone.utc


def test_factory_normalizes_metadata() -> None:
    aggregate = create_reconciliation(
        metadata={
            "Source System": "novapay",
            "Expected Count": 4,
        }
    )

    assert isinstance(
        aggregate.metadata,
        ReconciliationMetadata,
    )

    assert aggregate.metadata.canonical_dict() == {
        "expected_count": 4,
        "source_system": "novapay",
    }


def test_factory_accepts_none_metadata() -> None:
    aggregate = create_reconciliation(
        metadata=None,
    )

    assert isinstance(
        aggregate.metadata,
        ReconciliationMetadata,
    )
    assert aggregate.metadata.canonical_dict() == {}


@pytest.mark.parametrize(
    "count",
    [
        0,
        1,
        10,
        10_000,
    ],
)
def test_factory_accepts_non_negative_entry_count(
    count: int,
) -> None:
    aggregate = create_reconciliation(
        expected_entry_count=count,
    )

    assert aggregate.expected_entry_count == count


@pytest.mark.parametrize(
    "invalid",
    [
        -1,
        -100,
    ],
)
def test_factory_rejects_negative_entry_count(
    invalid: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_reconciliation(
            expected_entry_count=invalid,
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
def test_factory_rejects_invalid_entry_count_type(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        create_reconciliation(
            expected_entry_count=invalid,
        )


def test_factory_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        create_reconciliation(
            created_at=datetime(
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
        "2026-08-04T12:00:00Z",
        1,
        None,
        object(),
    ],
)
def test_factory_rejects_non_datetime(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a datetime",
    ):
        create_reconciliation(
            created_at=invalid,
        )


def test_direct_construction_normalizes_all_fields() -> None:
    aggregate = construct_reconciliation(
        reconciliation_id="  recon-001  ",
        reconciliation_type="Provider Report",
        status="Review Required",
        settlement_batch_id="  batch-001  ",
        expected_entry_count=0,
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
            5,
            tzinfo=timezone(
                timedelta(hours=10)
            ),
        ),
        version=3,
        metadata={
            "Review Reason": "provider mismatch",
        },
    )

    assert (
        aggregate.reconciliation_id.value
        == "recon-001"
    )
    assert (
        aggregate.reconciliation_type
        is ReconciliationType.PROVIDER_REPORT
    )
    assert (
        aggregate.status
        is ReconciliationStatus.REVIEW_REQUIRED
    )
    assert (
        aggregate.settlement_batch_id.value
        == "batch-001"
    )
    assert aggregate.expected_entry_count == 0
    assert aggregate.created_at == UTC_TIME
    assert aggregate.updated_at == (
        UTC_TIME + timedelta(minutes=5)
    )
    assert aggregate.version == 3
    assert aggregate.metadata.canonical_dict() == {
        "review_reason": "provider mismatch",
    }


@pytest.mark.parametrize(
    "status",
    list(ReconciliationStatus),
)
def test_direct_construction_supports_all_statuses(
    status: ReconciliationStatus,
) -> None:
    aggregate = construct_reconciliation(
        status=status,
    )

    assert aggregate.status is status


@pytest.mark.parametrize(
    "version",
    [
        1,
        2,
        10,
        1_000_000,
    ],
)
def test_direct_construction_accepts_positive_version(
    version: int,
) -> None:
    aggregate = construct_reconciliation(
        version=version,
    )

    assert aggregate.version == version


def test_direct_construction_rejects_zero_version() -> None:
    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        construct_reconciliation(
            version=0,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        -1,
        -100,
    ],
)
def test_direct_construction_rejects_negative_version(
    invalid: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        construct_reconciliation(
            version=invalid,
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
def test_direct_construction_rejects_invalid_version_type(
    invalid: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        construct_reconciliation(
            version=invalid,
        )


def test_direct_construction_rejects_reversed_chronology() -> None:
    with pytest.raises(
        ValueError,
        match="must not precede created_at",
    ):
        construct_reconciliation(
            created_at=UTC_TIME,
            updated_at=(
                UTC_TIME - timedelta(seconds=1)
            ),
        )


def test_direct_construction_accepts_equal_timestamps() -> None:
    aggregate = construct_reconciliation(
        created_at=UTC_TIME,
        updated_at=UTC_TIME,
    )

    assert (
        aggregate.created_at
        == aggregate.updated_at
    )


def test_direct_construction_accepts_later_updated_at() -> None:
    aggregate = construct_reconciliation(
        created_at=UTC_TIME,
        updated_at=(
            UTC_TIME + timedelta(hours=1)
        ),
    )

    assert (
        aggregate.updated_at
        > aggregate.created_at
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
    ],
)
def test_direct_construction_rejects_naive_timestamps(
    field_name: str,
) -> None:
    values: dict[str, object] = {
        field_name: datetime(
            2026,
            8,
            4,
            12,
            0,
        ),
    }

    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        construct_reconciliation(**values)


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
    ],
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
def test_direct_construction_rejects_invalid_timestamp_types(
    field_name: str,
    invalid: object,
) -> None:
    values: dict[str, object] = {
        field_name: invalid,
    }

    with pytest.raises(
        TypeError,
        match="must be a datetime",
    ):
        construct_reconciliation(**values)


@pytest.mark.parametrize(
    "status",
    [
        ReconciliationStatus.MATCHED,
        ReconciliationStatus.CLOSED,
        ReconciliationStatus.CANCELED,
        ReconciliationStatus.EXPIRED,
    ],
)
def test_terminal_status_classification(
    status: ReconciliationStatus,
) -> None:
    aggregate = construct_reconciliation(
        status=status,
    )

    assert aggregate.is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        ReconciliationStatus.DRAFT,
        ReconciliationStatus.OPEN,
        ReconciliationStatus.COLLECTING,
        ReconciliationStatus.COMPARING,
        ReconciliationStatus.PARTIALLY_MATCHED,
        ReconciliationStatus.UNMATCHED,
        ReconciliationStatus.EXCEPTION,
        ReconciliationStatus.REVIEW_REQUIRED,
    ],
)
def test_non_terminal_status_classification(
    status: ReconciliationStatus,
) -> None:
    aggregate = construct_reconciliation(
        status=status,
    )

    assert aggregate.is_terminal is False


@pytest.mark.parametrize(
    "status",
    list(ReconciliationStatus),
)
def test_is_draft_classification(
    status: ReconciliationStatus,
) -> None:
    aggregate = construct_reconciliation(
        status=status,
    )

    assert aggregate.is_draft is (
        status is ReconciliationStatus.DRAFT
    )


def test_canonical_dict_contract() -> None:
    aggregate = create_reconciliation(
        metadata={
            "source": "novapay",
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    assert aggregate.canonical_dict() == {
        "reconciliation_id": "recon-001",
        "reconciliation_type": "settlement_batch",
        "status": "draft",
        "settlement_batch_id": "batch-001",
        "expected_entry_count": 4,
        "created_at": "2026-08-04T12:00:00+00:00",
        "updated_at": "2026-08-04T12:00:00+00:00",
        "version": 1,
        "metadata": {
            "nested": {
                "values": [1, 2, 3],
            },
            "source": "novapay",
        },
    }


def test_canonical_dict_is_deterministic() -> None:
    aggregate = create_reconciliation(
        metadata={
            "zeta": 1,
            "alpha": 2,
        }
    )

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first == second


def test_canonical_dict_returns_fresh_top_level_payload() -> None:
    aggregate = create_reconciliation()

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first is not second


def test_canonical_dict_returns_fresh_metadata_payload() -> None:
    aggregate = create_reconciliation(
        metadata={
            "nested": {
                "value": 1,
            },
        }
    )

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first["metadata"] is not second["metadata"]
    assert (
        first["metadata"]["nested"]
        is not second["metadata"]["nested"]
    )


def test_canonical_dict_returns_fresh_nested_sequences() -> None:
    aggregate = create_reconciliation(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert (
        first["metadata"]["nested"]["values"]
        is not second["metadata"]["nested"]["values"]
    )


def test_serialized_payload_mutation_does_not_leak() -> None:
    aggregate = create_reconciliation(
        metadata={
            "nested": {
                "values": [1, 2, 3],
            },
        }
    )

    payload = aggregate.canonical_dict()
    payload["metadata"]["nested"]["values"].append(4)

    assert aggregate.canonical_dict()[
        "metadata"
    ]["nested"]["values"] == [1, 2, 3]


def test_source_metadata_mutation_does_not_leak() -> None:
    metadata: dict[str, Any] = {
        "nested": {
            "value": 1,
        },
    }

    aggregate = create_reconciliation(
        metadata=metadata,
    )

    metadata["nested"]["value"] = 2

    assert aggregate.metadata.canonical_dict() == {
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


def test_reconciliation_record_symbols_are_present() -> None:
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


def test_aggregate_has_no_operational_authority() -> None:
    names = {
        name
        for name in dir(
            SettlementReconciliation
        )
        if not name.startswith("__")
    }

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
        "compare",
        "match",
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

    for method_name in forbidden:
        assert method_name not in names


def test_aggregate_has_no_operational_dependencies() -> None:
    field_names = {
        field.name
        for field in fields(
            SettlementReconciliation
        )
    }

    forbidden = (
        "wallet",
        "wallet_repository",
        "ledger",
        "journal",
        "provider",
        "provider_client",
        "settlement_engine",
        "reconciliation_engine",
        "repository",
        "database",
        "credentials",
    )

    for field_name in forbidden:
        assert field_name not in field_names
