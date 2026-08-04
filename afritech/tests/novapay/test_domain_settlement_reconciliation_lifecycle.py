from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest

import afritech.novapay.domain.settlement_reconciliation as reconciliation

from afritech.novapay.domain.settlement_reconciliation import (
    ReconciliationStatus,
    SettlementReconciliation,
)


BASE_TIME = datetime(
    2026,
    8,
    4,
    12,
    0,
    tzinfo=timezone.utc,
)


def create_draft(
    *,
    reconciliation_id: str = "recon-001",
) -> SettlementReconciliation:
    return SettlementReconciliation.create(
        reconciliation_id=reconciliation_id,
        reconciliation_type="settlement_batch",
        settlement_batch_id="batch-001",
        expected_entry_count=2,
        created_at=BASE_TIME,
        metadata={
            "source": "novapay",
        },
    )


def create_open() -> SettlementReconciliation:
    return create_draft().open(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )


def create_collecting() -> SettlementReconciliation:
    return create_open().start_collecting(
        transitioned_at=BASE_TIME
        + timedelta(minutes=2)
    )


def create_comparing() -> SettlementReconciliation:
    return create_collecting().start_comparing(
        transitioned_at=BASE_TIME
        + timedelta(minutes=3)
    )


def create_matched() -> SettlementReconciliation:
    return create_comparing().mark_matched(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )


def create_partially_matched() -> SettlementReconciliation:
    return create_comparing().mark_partially_matched(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )


def create_unmatched() -> SettlementReconciliation:
    return create_comparing().mark_unmatched(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )


def create_exception() -> SettlementReconciliation:
    return create_comparing().mark_exception(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )


def create_review_required() -> SettlementReconciliation:
    return create_comparing().require_review(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )


def create_closed() -> SettlementReconciliation:
    return create_matched().close(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )


def create_canceled() -> SettlementReconciliation:
    return create_draft().cancel(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )


def create_expired() -> SettlementReconciliation:
    return create_open().expire(
        transitioned_at=BASE_TIME
        + timedelta(minutes=2)
    )


def test_lifecycle_method_contract() -> None:
    required = {
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
    }

    names = {
        name
        for name in dir(SettlementReconciliation)
        if not name.startswith("__")
    }

    assert required.issubset(names)


def test_draft_to_open_transition() -> None:
    draft = create_draft()

    opened = draft.open(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )

    assert draft.status is ReconciliationStatus.DRAFT
    assert opened.status is ReconciliationStatus.OPEN
    assert draft.version == 1
    assert opened.version == 2
    assert draft.updated_at == BASE_TIME
    assert opened.updated_at == (
        BASE_TIME + timedelta(minutes=1)
    )
    assert opened is not draft


def test_open_to_collecting_transition() -> None:
    opened = create_open()

    collecting = opened.start_collecting(
        transitioned_at=BASE_TIME
        + timedelta(minutes=2)
    )

    assert opened.status is ReconciliationStatus.OPEN
    assert collecting.status is ReconciliationStatus.COLLECTING
    assert collecting.version == opened.version + 1


def test_collecting_to_comparing_transition() -> None:
    collecting = create_collecting()

    comparing = collecting.start_comparing(
        transitioned_at=BASE_TIME
        + timedelta(minutes=3)
    )

    assert (
        collecting.status
        is ReconciliationStatus.COLLECTING
    )
    assert (
        comparing.status
        is ReconciliationStatus.COMPARING
    )
    assert comparing.version == collecting.version + 1


@pytest.mark.parametrize(
    ("method_name", "expected_status"),
    [
        (
            "mark_matched",
            ReconciliationStatus.MATCHED,
        ),
        (
            "mark_partially_matched",
            ReconciliationStatus.PARTIALLY_MATCHED,
        ),
        (
            "mark_unmatched",
            ReconciliationStatus.UNMATCHED,
        ),
        (
            "mark_exception",
            ReconciliationStatus.EXCEPTION,
        ),
        (
            "require_review",
            ReconciliationStatus.REVIEW_REQUIRED,
        ),
    ],
)
def test_comparing_classification_transitions(
    method_name: str,
    expected_status: ReconciliationStatus,
) -> None:
    comparing = create_comparing()

    method = getattr(
        comparing,
        method_name,
    )

    result = method(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )

    assert result.status is expected_status
    assert result.version == comparing.version + 1
    assert result.updated_at == (
        BASE_TIME + timedelta(minutes=4)
    )
    assert comparing.status is ReconciliationStatus.COMPARING


def test_matched_to_closed_transition() -> None:
    matched = create_matched()

    closed = matched.close(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert matched.status is ReconciliationStatus.MATCHED
    assert closed.status is ReconciliationStatus.CLOSED
    assert closed.version == matched.version + 1
    assert closed.is_terminal is True


@pytest.mark.parametrize(
    "factory",
    [
        create_partially_matched,
        create_unmatched,
        create_exception,
    ],
)
def test_outcome_to_review_required_transition(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
) -> None:
    aggregate = factory()

    reviewed = aggregate.require_review(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert (
        reviewed.status
        is ReconciliationStatus.REVIEW_REQUIRED
    )
    assert reviewed.version == aggregate.version + 1


@pytest.mark.parametrize(
    "factory",
    [
        create_partially_matched,
        create_unmatched,
        create_exception,
    ],
)
def test_outcome_can_close(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
) -> None:
    aggregate = factory()

    closed = aggregate.close(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert closed.status is ReconciliationStatus.CLOSED
    assert closed.is_terminal is True


def test_review_required_can_return_to_collecting() -> None:
    review = create_review_required()

    collecting = review.start_collecting(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert (
        collecting.status
        is ReconciliationStatus.COLLECTING
    )


def test_review_required_can_return_to_comparing() -> None:
    review = create_review_required()

    comparing = review.start_comparing(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert (
        comparing.status
        is ReconciliationStatus.COMPARING
    )


def test_review_required_can_close() -> None:
    review = create_review_required()

    closed = review.close(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert closed.status is ReconciliationStatus.CLOSED


def test_review_required_can_cancel() -> None:
    review = create_review_required()

    canceled = review.cancel(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert canceled.status is ReconciliationStatus.CANCELED


def test_review_required_can_expire() -> None:
    review = create_review_required()

    expired = review.expire(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert expired.status is ReconciliationStatus.EXPIRED


def test_draft_can_cancel() -> None:
    canceled = create_draft().cancel(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )

    assert canceled.status is ReconciliationStatus.CANCELED
    assert canceled.is_terminal is True


@pytest.mark.parametrize(
    "factory",
    [
        create_open,
        create_collecting,
        create_comparing,
        create_review_required,
    ],
)
def test_active_states_can_cancel(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
) -> None:
    aggregate = factory()

    canceled = aggregate.cancel(
        transitioned_at=aggregate.updated_at
        + timedelta(minutes=1)
    )

    assert canceled.status is ReconciliationStatus.CANCELED
    assert canceled.is_terminal is True


@pytest.mark.parametrize(
    "factory",
    [
        create_open,
        create_collecting,
        create_comparing,
        create_review_required,
    ],
)
def test_active_states_can_expire(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
) -> None:
    aggregate = factory()

    expired = aggregate.expire(
        transitioned_at=aggregate.updated_at
        + timedelta(minutes=1)
    )

    assert expired.status is ReconciliationStatus.EXPIRED
    assert expired.is_terminal is True


@pytest.mark.parametrize(
    ("factory", "method_name"),
    [
        (create_draft, "start_collecting"),
        (create_draft, "start_comparing"),
        (create_draft, "mark_matched"),
        (create_draft, "mark_partially_matched"),
        (create_draft, "mark_unmatched"),
        (create_draft, "mark_exception"),
        (create_draft, "require_review"),
        (create_draft, "close"),
        (create_draft, "expire"),
        (create_open, "open"),
        (create_open, "start_comparing"),
        (create_open, "mark_matched"),
        (create_open, "close"),
        (create_collecting, "open"),
        (create_collecting, "mark_matched"),
        (create_collecting, "close"),
        (create_comparing, "open"),
        (create_comparing, "start_collecting"),
        (create_matched, "open"),
        (create_matched, "require_review"),
        (create_matched, "cancel"),
        (create_matched, "expire"),
    ],
)
def test_invalid_transitions_are_rejected(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
    method_name: str,
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="invalid settlement reconciliation transition",
    ):
        method(
            transitioned_at=aggregate.updated_at
            + timedelta(minutes=1)
        )


@pytest.mark.parametrize(
    "factory",
    [
        create_closed,
        create_canceled,
        create_expired,
    ],
)
@pytest.mark.parametrize(
    "method_name",
    [
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
    ],
)
def test_terminal_states_reject_all_transitions(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
    method_name: str,
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="invalid settlement reconciliation transition",
    ):
        method(
            transitioned_at=aggregate.updated_at
            + timedelta(minutes=1)
        )


@pytest.mark.parametrize(
    "invalid",
    [
        datetime(
            2026,
            8,
            4,
            12,
            0,
        ),
        "2026-08-04T12:00:00Z",
        1,
        True,
        None,
        object(),
    ],
)
def test_transition_rejects_invalid_timestamp(
    invalid: object,
) -> None:
    draft = create_draft()

    with pytest.raises((TypeError, ValueError)):
        draft.open(
            transitioned_at=invalid,
        )


def test_transition_rejects_timestamp_regression() -> None:
    opened = create_open()

    with pytest.raises(
        ValueError,
        match="must not precede updated_at",
    ):
        opened.start_collecting(
            transitioned_at=opened.updated_at
            - timedelta(seconds=1)
        )


def test_transition_accepts_equal_timestamp() -> None:
    draft = create_draft()

    opened = draft.open(
        transitioned_at=draft.updated_at,
    )

    assert opened.updated_at == draft.updated_at
    assert opened.version == draft.version + 1


def test_transition_normalizes_timestamp_to_utc() -> None:
    local_timezone = timezone(
        timedelta(hours=10)
    )

    draft = create_draft()

    opened = draft.open(
        transitioned_at=datetime(
            2026,
            8,
            4,
            22,
            1,
            tzinfo=local_timezone,
        )
    )

    assert opened.updated_at == (
        BASE_TIME + timedelta(minutes=1)
    )
    assert opened.updated_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "factory",
    [
        create_draft,
        create_open,
        create_collecting,
        create_comparing,
        create_matched,
        create_partially_matched,
        create_unmatched,
        create_exception,
        create_review_required,
        create_closed,
        create_canceled,
        create_expired,
    ],
)
def test_metadata_update_preserves_status(
    factory: Callable[
        [],
        SettlementReconciliation,
    ],
) -> None:
    aggregate = factory()

    updated = aggregate.update_metadata(
        {
            "updated": True,
        },
        updated_at=aggregate.updated_at
        + timedelta(minutes=1),
    )

    assert updated.status is aggregate.status
    assert updated.version == aggregate.version + 1
    assert updated.metadata.canonical_dict() == {
        "updated": True,
    }


def test_metadata_update_preserves_original_aggregate() -> None:
    aggregate = create_draft()

    updated = aggregate.update_metadata(
        {
            "Review Reason": "provider mismatch",
        },
        updated_at=BASE_TIME
        + timedelta(minutes=1),
    )

    assert aggregate.metadata.canonical_dict() == {
        "source": "novapay",
    }

    assert updated.metadata.canonical_dict() == {
        "review_reason": "provider mismatch",
    }

    assert aggregate.version == 1
    assert updated.version == 2


def test_metadata_update_accepts_none() -> None:
    aggregate = create_draft()

    updated = aggregate.update_metadata(
        None,
        updated_at=BASE_TIME
        + timedelta(minutes=1),
    )

    assert updated.metadata.canonical_dict() == {}


@pytest.mark.parametrize(
    "invalid",
    [
        "metadata",
        1,
        True,
        [],
        object(),
    ],
)
def test_metadata_update_rejects_invalid_metadata(
    invalid: object,
) -> None:
    aggregate = create_draft()

    with pytest.raises(TypeError):
        aggregate.update_metadata(
            invalid,
            updated_at=BASE_TIME
            + timedelta(minutes=1),
        )


def test_metadata_update_rejects_timestamp_regression() -> None:
    aggregate = create_open()

    with pytest.raises(
        ValueError,
        match="must not precede updated_at",
    ):
        aggregate.update_metadata(
            {},
            updated_at=aggregate.updated_at
            - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "invalid",
    [
        datetime(
            2026,
            8,
            4,
            12,
            1,
        ),
        "timestamp",
        1,
        None,
        object(),
    ],
)
def test_metadata_update_rejects_invalid_timestamp(
    invalid: object,
) -> None:
    aggregate = create_draft()

    with pytest.raises((TypeError, ValueError)):
        aggregate.update_metadata(
            {},
            updated_at=invalid,
        )


def test_transition_preserves_identity_and_structure() -> None:
    draft = create_draft()

    opened = draft.open(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )

    assert opened.reconciliation_id is draft.reconciliation_id
    assert opened.reconciliation_type is draft.reconciliation_type
    assert opened.settlement_batch_id is draft.settlement_batch_id
    assert (
        opened.expected_entry_count
        == draft.expected_entry_count
    )
    assert opened.created_at == draft.created_at
    assert opened.metadata is draft.metadata


def test_full_matched_lifecycle_version_sequence() -> None:
    draft = create_draft()

    opened = draft.open(
        transitioned_at=BASE_TIME
        + timedelta(minutes=1)
    )

    collecting = opened.start_collecting(
        transitioned_at=BASE_TIME
        + timedelta(minutes=2)
    )

    comparing = collecting.start_comparing(
        transitioned_at=BASE_TIME
        + timedelta(minutes=3)
    )

    matched = comparing.mark_matched(
        transitioned_at=BASE_TIME
        + timedelta(minutes=4)
    )

    closed = matched.close(
        transitioned_at=BASE_TIME
        + timedelta(minutes=5)
    )

    assert [
        draft.version,
        opened.version,
        collecting.version,
        comparing.version,
        matched.version,
        closed.version,
    ] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_full_lifecycle_serialization_contract() -> None:
    closed = create_closed()

    assert closed.canonical_dict() == {
        "reconciliation_id": "recon-001",
        "reconciliation_type": "settlement_batch",
        "status": "closed",
        "settlement_batch_id": "batch-001",
        "expected_entry_count": 2,
        "created_at": "2026-08-04T12:00:00+00:00",
        "updated_at": "2026-08-04T12:05:00+00:00",
        "version": 6,
        "metadata": {
            "source": "novapay",
        },
    }


def test_lifecycle_has_no_execution_authority() -> None:
    names = {
        name
        for name in dir(SettlementReconciliation)
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
