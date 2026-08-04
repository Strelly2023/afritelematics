from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

import pytest

import afritech.novapay.domain.settlement_batch as settlement_batch
from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.settlement_batch import (
    SettlementBatch,
    SettlementBatchStatus,
    SettlementMetadata,
    SettlementParticipant,
    SettlementReference,
    SettlementWindow,
)


CREATED_AT = datetime(
    2026,
    8,
    4,
    3,
    20,
    tzinfo=timezone.utc,
)

WINDOW_CLOSE = CREATED_AT + timedelta(hours=4)


def currency(code: str) -> Currency:
    parse = getattr(Currency, "parse", None)

    if callable(parse):
        try:
            result = parse(code)
        except (TypeError, ValueError):
            pass
        else:
            if isinstance(result, Currency):
                return result

    for factory in (
        lambda: Currency(code),
        lambda: Currency(code=code),
    ):
        try:
            result = factory()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Currency):
            return result

    raise AssertionError(
        f"unable to construct Currency for {code}"
    )


def money(
    amount: str,
    code: str = "AUD",
) -> Money:
    decimal_amount = Decimal(amount)
    currency_value = currency(code)
    factory = getattr(Money, "of", None)

    attempts = []

    if callable(factory):
        attempts.extend(
            (
                lambda: factory(
                    decimal_amount,
                    currency_value,
                ),
                lambda: factory(
                    amount=decimal_amount,
                    currency=currency_value,
                ),
            )
        )

    attempts.extend(
        (
            lambda: Money(
                amount=decimal_amount,
                currency=currency_value,
            ),
            lambda: Money(
                decimal_amount,
                currency_value,
            ),
        )
    )

    for attempt in attempts:
        try:
            result = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Money):
            return result

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def settlement_window(
    *,
    closes_at: datetime = WINDOW_CLOSE,
) -> SettlementWindow:
    return SettlementWindow(
        opens_at=CREATED_AT,
        closes_at=closes_at,
        cutoff_at=closes_at - timedelta(hours=1),
        timezone_name="Australia/Melbourne",
    )


def participant() -> SettlementParticipant:
    return SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="settlement account",
        account_reference="account-001",
        currency_code="AUD",
        jurisdiction_code="AU",
    )


def reference() -> SettlementReference:
    return SettlementReference.create(
        reference_type="remittance",
        reference_id="remittance-001",
    )


def draft_batch(
    *,
    identifier: str = "settlement-batch-001",
    metadata: object = None,
) -> SettlementBatch:
    return SettlementBatch.create(
        batch_id=identifier,
        batch_type="netting",
        window=settlement_window(),
        settlement_currency_code="AUD",
        gross_amount=money("1000.00"),
        net_amount=money("950.00"),
        participants=(participant(),),
        references=(reference(),),
        entry_count=1,
        created_at=CREATED_AT,
        metadata=(
            {
                "source_system": "novapay",
            }
            if metadata is None
            else metadata
        ),
    )


def processing_batch() -> SettlementBatch:
    return (
        draft_batch()
        .validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        )
        .open(
            changed_at=CREATED_AT
            + timedelta(minutes=2)
        )
        .mark_ready(
            changed_at=CREATED_AT
            + timedelta(minutes=3)
        )
        .mark_processing(
            changed_at=CREATED_AT
            + timedelta(minutes=4)
        )
    )


def completed_batch() -> SettlementBatch:
    return processing_batch().complete(
        changed_at=CREATED_AT
        + timedelta(minutes=5)
    )


def partially_completed_batch() -> SettlementBatch:
    return processing_batch().partially_complete(
        changed_at=CREATED_AT
        + timedelta(minutes=5)
    )


def assert_preserved(
    before: SettlementBatch,
    after: SettlementBatch,
) -> None:
    assert after is not before
    assert after.batch_id is before.batch_id
    assert after.gross_amount is before.gross_amount
    assert after.net_amount is before.net_amount
    assert after.participants == before.participants
    assert after.references == before.references
    assert after.entry_count == before.entry_count
    assert after.created_at == before.created_at
    assert after.version == before.version + 1


def test_lifecycle_method_inventory() -> None:
    required = {
        "validate",
        "open",
        "mark_ready",
        "mark_processing",
        "complete",
        "partially_complete",
        "fail",
        "cancel",
        "expire",
        "reconcile",
        "update_metadata",
        "update_window",
    }

    assert required.issubset(
        set(dir(SettlementBatch))
    )


def test_complete_successful_transition_path() -> None:
    draft = draft_batch()

    validated = draft.validate(
        changed_at=CREATED_AT + timedelta(minutes=1)
    )

    opened = validated.open(
        changed_at=CREATED_AT + timedelta(minutes=2)
    )

    ready = opened.mark_ready(
        changed_at=CREATED_AT + timedelta(minutes=3)
    )

    processing = ready.mark_processing(
        changed_at=CREATED_AT + timedelta(minutes=4)
    )

    completed = processing.complete(
        changed_at=CREATED_AT + timedelta(minutes=5)
    )

    reconciled = completed.reconcile(
        changed_at=CREATED_AT + timedelta(minutes=6)
    )

    assert [
        value.status
        for value in (
            draft,
            validated,
            opened,
            ready,
            processing,
            completed,
            reconciled,
        )
    ] == [
        SettlementBatchStatus.DRAFT,
        SettlementBatchStatus.VALIDATED,
        SettlementBatchStatus.OPEN,
        SettlementBatchStatus.READY,
        SettlementBatchStatus.PROCESSING,
        SettlementBatchStatus.COMPLETE,
        SettlementBatchStatus.RECONCILED,
    ]

    assert [
        value.version
        for value in (
            draft,
            validated,
            opened,
            ready,
            processing,
            completed,
            reconciled,
        )
    ] == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.parametrize(
    (
        "builder",
        "transition",
        "expected_status",
    ),
    [
        (
            lambda: draft_batch(),
            lambda value: value.validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
            SettlementBatchStatus.VALIDATED,
        ),
        (
            lambda: draft_batch().validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
            lambda value: value.open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            ),
            SettlementBatchStatus.OPEN,
        ),
        (
            lambda: (
                draft_batch()
                .validate(
                    changed_at=CREATED_AT
                    + timedelta(minutes=1)
                )
                .open(
                    changed_at=CREATED_AT
                    + timedelta(minutes=2)
                )
            ),
            lambda value: value.mark_ready(
                changed_at=CREATED_AT
                + timedelta(minutes=3)
            ),
            SettlementBatchStatus.READY,
        ),
        (
            lambda: (
                draft_batch()
                .validate(
                    changed_at=CREATED_AT
                    + timedelta(minutes=1)
                )
                .open(
                    changed_at=CREATED_AT
                    + timedelta(minutes=2)
                )
                .mark_ready(
                    changed_at=CREATED_AT
                    + timedelta(minutes=3)
                )
            ),
            lambda value: value.mark_processing(
                changed_at=CREATED_AT
                + timedelta(minutes=4)
            ),
            SettlementBatchStatus.PROCESSING,
        ),
        (
            processing_batch,
            lambda value: value.complete(
                changed_at=CREATED_AT
                + timedelta(minutes=5)
            ),
            SettlementBatchStatus.COMPLETE,
        ),
        (
            processing_batch,
            lambda value: value.partially_complete(
                changed_at=CREATED_AT
                + timedelta(minutes=5)
            ),
            SettlementBatchStatus.PARTIALLY_COMPLETE,
        ),
        (
            processing_batch,
            lambda value: value.fail(
                changed_at=CREATED_AT
                + timedelta(minutes=5)
            ),
            SettlementBatchStatus.FAILURE,
        ),
        (
            completed_batch,
            lambda value: value.reconcile(
                changed_at=CREATED_AT
                + timedelta(minutes=6)
            ),
            SettlementBatchStatus.RECONCILED,
        ),
        (
            partially_completed_batch,
            lambda value: value.reconcile(
                changed_at=CREATED_AT
                + timedelta(minutes=6)
            ),
            SettlementBatchStatus.RECONCILED,
        ),
    ],
)
def test_valid_transition_matrix(
    builder: Callable[[], SettlementBatch],
    transition: Callable[
        [SettlementBatch],
        SettlementBatch,
    ],
    expected_status: SettlementBatchStatus,
) -> None:
    before = builder()
    after = transition(before)

    assert after.status is expected_status
    assert_preserved(before, after)


@pytest.mark.parametrize(
    "builder",
    [
        draft_batch,
        lambda: draft_batch().validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
            .mark_ready(
                changed_at=CREATED_AT
                + timedelta(minutes=3)
            )
        ),
    ],
)
def test_cancellation_allowed_before_processing(
    builder: Callable[[], SettlementBatch],
) -> None:
    before = builder()

    after = before.cancel(
        changed_at=before.updated_at
        + timedelta(minutes=1)
    )

    assert after.status is SettlementBatchStatus.CANCELED
    assert after.is_terminal is True
    assert_preserved(before, after)


@pytest.mark.parametrize(
    "builder",
    [
        draft_batch,
        lambda: draft_batch().validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
            .mark_ready(
                changed_at=CREATED_AT
                + timedelta(minutes=3)
            )
        ),
        processing_batch,
    ],
)
def test_expiry_allowed_after_window_close(
    builder: Callable[[], SettlementBatch],
) -> None:
    before = builder()

    after = before.expire(
        changed_at=WINDOW_CLOSE
    )

    assert after.status is SettlementBatchStatus.EXPIRED
    assert after.is_terminal is True
    assert_preserved(before, after)


@pytest.mark.parametrize(
    (
        "builder",
        "operation",
    ),
    [
        (
            draft_batch,
            lambda value: value.open(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.mark_ready(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.mark_processing(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.complete(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.partially_complete(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.fail(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            draft_batch,
            lambda value: value.reconcile(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            ),
        ),
        (
            processing_batch,
            lambda value: value.cancel(
                changed_at=CREATED_AT
                + timedelta(minutes=5)
            ),
        ),
        (
            completed_batch,
            lambda value: value.complete(
                changed_at=CREATED_AT
                + timedelta(minutes=6)
            ),
        ),
        (
            completed_batch,
            lambda value: value.fail(
                changed_at=CREATED_AT
                + timedelta(minutes=6)
            ),
        ),
    ],
)
def test_invalid_transition_matrix(
    builder: Callable[[], SettlementBatch],
    operation: Callable[
        [SettlementBatch],
        SettlementBatch,
    ],
) -> None:
    value = builder()

    with pytest.raises(
        ValueError,
        match="invalid settlement batch transition",
    ):
        operation(value)


def test_transition_metadata_is_merged() -> None:
    draft = draft_batch(
        metadata={
            "source_system": "novapay",
            "attempt": 1,
        }
    )

    validated = draft.validate(
        changed_at=CREATED_AT + timedelta(minutes=1),
        metadata={
            "validation_result": "passed",
            "attempt": 2,
        },
    )

    assert validated.metadata.values == {
        "attempt": 2,
        "source_system": "novapay",
        "validation_result": "passed",
    }

    assert draft.metadata.values == {
        "attempt": 1,
        "source_system": "novapay",
    }


def test_transition_metadata_rejects_sensitive_keys() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        draft_batch().validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1),
            metadata={
                "authorization": "secret",
            },
        )


def test_same_timestamp_transition_is_allowed() -> None:
    draft = draft_batch()

    validated = draft.validate(
        changed_at=draft.updated_at
    )

    assert validated.updated_at == draft.updated_at
    assert validated.version == draft.version + 1


def test_changed_at_before_updated_at_is_rejected() -> None:
    validated = draft_batch().validate(
        changed_at=CREATED_AT
        + timedelta(minutes=1)
    )

    with pytest.raises(
        ValueError,
        match="must not precede updated_at",
    ):
        validated.open(
            changed_at=CREATED_AT
        )


def test_naive_changed_at_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        draft_batch().validate(
            changed_at=CREATED_AT.replace(
                tzinfo=None
            )
        )


def test_expiry_before_window_close_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot expire before",
    ):
        draft_batch().expire(
            changed_at=WINDOW_CLOSE
            - timedelta(microseconds=1)
        )


def test_expiry_at_window_close_is_allowed() -> None:
    expired = draft_batch().expire(
        changed_at=WINDOW_CLOSE
    )

    assert expired.status is SettlementBatchStatus.EXPIRED


def test_metadata_update_merges_values() -> None:
    draft = draft_batch(
        metadata={
            "source_system": "novapay",
            "attempt": 1,
        }
    )

    updated = draft.update_metadata(
        metadata={
            "attempt": 2,
            "review_state": "approved",
        },
        changed_at=CREATED_AT + timedelta(minutes=1),
    )

    assert updated.metadata.values == {
        "attempt": 2,
        "review_state": "approved",
        "source_system": "novapay",
    }

    assert_preserved(draft, updated)


def test_metadata_update_at_same_timestamp_is_allowed() -> None:
    draft = draft_batch()

    updated = draft.update_metadata(
        metadata={
            "review_state": "approved",
        },
        changed_at=draft.updated_at,
    )

    assert updated.updated_at == draft.updated_at
    assert updated.version == draft.version + 1


def test_metadata_noop_is_rejected() -> None:
    draft = draft_batch()

    with pytest.raises(
        ValueError,
        match="must change at least one value",
    ):
        draft.update_metadata(
            metadata={
                "source_system": "novapay",
            },
            changed_at=CREATED_AT
            + timedelta(minutes=1),
        )


@pytest.mark.parametrize(
    "builder",
    [
        completed_batch,
        partially_completed_batch,
        lambda: processing_batch().fail(
            changed_at=CREATED_AT
            + timedelta(minutes=5)
        ),
        lambda: draft_batch().cancel(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        ),
        lambda: draft_batch().expire(
            changed_at=WINDOW_CLOSE
        ),
        lambda: completed_batch().reconcile(
            changed_at=CREATED_AT
            + timedelta(minutes=6)
        ),
    ],
)
def test_terminal_metadata_updates_are_rejected(
    builder: Callable[[], SettlementBatch],
) -> None:
    value = builder()

    with pytest.raises(
        ValueError,
        match="terminal settlement batch metadata",
    ):
        value.update_metadata(
            metadata={
                "late_change": "rejected",
            },
            changed_at=value.updated_at
            + timedelta(minutes=1),
        )


def test_window_update_before_processing() -> None:
    draft = draft_batch()

    new_window = settlement_window(
        closes_at=WINDOW_CLOSE + timedelta(hours=1)
    )

    updated = draft.update_window(
        window=new_window,
        changed_at=CREATED_AT
        + timedelta(minutes=1),
    )

    assert updated.window == new_window
    assert draft.window != new_window
    assert_preserved(draft, updated)


@pytest.mark.parametrize(
    "builder",
    [
        draft_batch,
        lambda: draft_batch().validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
        ),
        lambda: (
            draft_batch()
            .validate(
                changed_at=CREATED_AT
                + timedelta(minutes=1)
            )
            .open(
                changed_at=CREATED_AT
                + timedelta(minutes=2)
            )
            .mark_ready(
                changed_at=CREATED_AT
                + timedelta(minutes=3)
            )
        ),
    ],
)
def test_window_update_allowed_before_processing(
    builder: Callable[[], SettlementBatch],
) -> None:
    value = builder()

    new_window = settlement_window(
        closes_at=WINDOW_CLOSE + timedelta(hours=1)
    )

    updated = value.update_window(
        window=new_window,
        changed_at=value.updated_at
        + timedelta(minutes=1),
    )

    assert updated.window == new_window
    assert updated.version == value.version + 1


def test_window_update_during_processing_is_rejected() -> None:
    value = processing_batch()

    with pytest.raises(
        ValueError,
        match="before processing",
    ):
        value.update_window(
            window=settlement_window(
                closes_at=WINDOW_CLOSE
                + timedelta(hours=1)
            ),
            changed_at=value.updated_at
            + timedelta(minutes=1),
        )


def test_window_noop_is_rejected() -> None:
    value = draft_batch()

    with pytest.raises(
        ValueError,
        match="must change the window",
    ):
        value.update_window(
            window=value.window,
            changed_at=CREATED_AT
            + timedelta(minutes=1),
        )


def test_window_update_rejects_invalid_type() -> None:
    value = draft_batch()

    with pytest.raises(
        TypeError,
        match="SettlementWindow",
    ):
        value.update_window(
            window="invalid",  # type: ignore[arg-type]
            changed_at=CREATED_AT
            + timedelta(minutes=1),
        )


def test_window_must_not_close_before_creation() -> None:
    value = draft_batch()

    invalid_window = SettlementWindow(
        opens_at=CREATED_AT
        - timedelta(hours=2),
        closes_at=CREATED_AT
        - timedelta(hours=1),
    )

    with pytest.raises(
        ValueError,
        match="must not close before batch creation",
    ):
        value.update_window(
            window=invalid_window,
            changed_at=CREATED_AT
            + timedelta(minutes=1),
        )


def test_lifecycle_preserves_canonical_money_identity() -> None:
    draft = draft_batch()

    completed = (
        draft.validate(
            changed_at=CREATED_AT
            + timedelta(minutes=1)
        )
        .open(
            changed_at=CREATED_AT
            + timedelta(minutes=2)
        )
        .mark_ready(
            changed_at=CREATED_AT
            + timedelta(minutes=3)
        )
        .mark_processing(
            changed_at=CREATED_AT
            + timedelta(minutes=4)
        )
        .complete(
            changed_at=CREATED_AT
            + timedelta(minutes=5)
        )
    )

    assert completed.gross_amount is draft.gross_amount
    assert completed.net_amount is draft.net_amount


def test_lifecycle_preserves_batch_identity() -> None:
    draft = draft_batch()

    validated = draft.validate(
        changed_at=CREATED_AT
        + timedelta(minutes=1)
    )

    assert validated.batch_id is draft.batch_id


def test_lifecycle_serialization_is_fresh() -> None:
    value = completed_batch()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["window"] is not second["window"]
    assert first["gross_amount"] is not second["gross_amount"]
    assert first["net_amount"] is not second["net_amount"]
    assert first["participants"] is not second["participants"]
    assert first["references"] is not second["references"]
    assert first["metadata"] is not second["metadata"]


def test_lifecycle_metadata_is_immutable() -> None:
    value = draft_batch().validate(
        changed_at=CREATED_AT
        + timedelta(minutes=1),
        metadata={
            "validation_result": "passed",
        },
    )

    assert isinstance(
        value.metadata,
        SettlementMetadata,
    )

    with pytest.raises(TypeError):
        value.metadata.values[
            "validation_result"
        ] = "changed"  # type: ignore[index]


def test_lifecycle_domain_remains_internal() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    import afritech.novapay.domain.settlement_batch as settlement_batch

    for symbol in settlement_batch.__all__:
        assert symbol in domain.__all__
        assert symbol in novapay.__all__
        assert hasattr(domain, symbol)
        assert hasattr(novapay, symbol)
        assert getattr(domain, symbol) is getattr(
            settlement_batch,
            symbol,
        )
        assert getattr(novapay, symbol) is getattr(
            settlement_batch,
            symbol,
        )


def test_lifecycle_has_no_execution_authority() -> None:
    names = {
        name
        for name in dir(SettlementBatch)
        if not name.startswith("__")
    }

    for forbidden in (
        "authorize",
        "reserve",
        "reserve_funds",
        "debit",
        "credit",
        "post",
        "post_entry",
        "execute",
        "settle",
        "clear",
        "net",
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
    ):
        assert forbidden not in names


def test_lifecycle_has_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(SettlementBatch)
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "provider_client",
        "settlement_engine",
        "reconciliation_engine",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names


def test_module_all_contract_is_unchanged() -> None:
    assert "SettlementBatch" in settlement_batch.__all__
    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )
    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )
