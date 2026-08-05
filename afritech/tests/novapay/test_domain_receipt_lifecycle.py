from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest

import afritech.novapay.domain.receipt as receipt
from afritech.novapay.domain.receipt import (
    Receipt,
    ReceiptMetadata,
    ReceiptParty,
    ReceiptStatus,
)


BASE_TIME = datetime(
    2026,
    8,
    5,
    0,
    0,
    tzinfo=timezone.utc,
)


def at(hours: int) -> datetime:
    return BASE_TIME + timedelta(
        hours=hours
    )


def issuer() -> ReceiptParty:
    return ReceiptParty(
        party_id="issuer-001",
        party_type="issuer",
        display_name="NovaPay Issuer",
        external_reference="business-001",
        metadata={},
    )


def draft_receipt(
    *,
    receipt_id: str = "receipt-001",
) -> Receipt:
    return Receipt.create(
        receipt_id=receipt_id,
        receipt_type="payment",
        format="structured",
        issuer=issuer(),
        recipient=None,
        currency_code="AUD",
        created_at=at(0),
    )


def prepared_receipt() -> Receipt:
    return draft_receipt().prepare(
        updated_at=at(1),
    )


def issued_receipt() -> Receipt:
    return prepared_receipt().issue(
        issued_at=at(2),
    )


def delivered_receipt() -> Receipt:
    return issued_receipt().mark_delivered(
        delivered_at=at(3),
    )


def canceled_receipt() -> Receipt:
    return draft_receipt().cancel(
        updated_at=at(1),
    )


def voided_receipt() -> Receipt:
    return issued_receipt().void(
        updated_at=at(3),
    )


def expired_receipt() -> Receipt:
    return issued_receipt().expire(
        expired_at=at(3),
    )


def superseded_receipt() -> Receipt:
    return issued_receipt().supersede(
        updated_at=at(3),
    )


def test_canonical_cancellation_vocabulary() -> None:
    assert ReceiptStatus.CANCELED.value == "canceled"
    assert ReceiptStatus.CANCELED.is_terminal is True
    assert not hasattr(
        ReceiptStatus,
        "CANCELLED",
    )


@pytest.mark.parametrize(
    "method_name",
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
def test_lifecycle_method_inventory(
    method_name: str,
) -> None:
    assert hasattr(
        Receipt,
        method_name,
    )
    assert callable(
        getattr(
            Receipt,
            method_name,
        )
    )


def test_prepare_transitions_draft_to_prepared() -> None:
    original = draft_receipt()

    updated = original.prepare(
        updated_at=at(1),
    )

    assert original.status is ReceiptStatus.DRAFT
    assert updated.status is ReceiptStatus.PREPARED
    assert original.version == 1
    assert updated.version == 2
    assert original.updated_at == at(0)
    assert updated.updated_at == at(1)
    assert original is not updated


def test_issue_transitions_prepared_to_issued() -> None:
    original = prepared_receipt()

    updated = original.issue(
        issued_at=at(2),
    )

    assert original.status is ReceiptStatus.PREPARED
    assert updated.status is ReceiptStatus.ISSUED
    assert updated.issued_at == at(2)
    assert updated.updated_at == at(2)
    assert updated.version == original.version + 1
    assert original is not updated


def test_issue_accepts_separate_update_timestamp() -> None:
    original = prepared_receipt()

    updated = original.issue(
        issued_at=at(2),
        updated_at=at(3),
    )

    assert updated.status is ReceiptStatus.ISSUED
    assert updated.issued_at == at(2)
    assert updated.updated_at == at(3)


def test_mark_delivered_transitions_issued_to_delivered() -> None:
    original = issued_receipt()

    updated = original.mark_delivered(
        delivered_at=at(3),
    )

    assert original.status is ReceiptStatus.ISSUED
    assert updated.status is ReceiptStatus.DELIVERED
    assert updated.issued_at == at(2)
    assert updated.delivered_at == at(3)
    assert updated.updated_at == at(3)
    assert updated.version == original.version + 1


def test_delivery_accepts_separate_update_timestamp() -> None:
    original = issued_receipt()

    updated = original.mark_delivered(
        delivered_at=at(3),
        updated_at=at(4),
    )

    assert updated.delivered_at == at(3)
    assert updated.updated_at == at(4)


@pytest.mark.parametrize(
    "factory",
    [
        draft_receipt,
        prepared_receipt,
    ],
)
def test_cancel_accepts_pre_issue_states(
    factory: Callable[[], Receipt],
) -> None:
    original = factory()

    updated = original.cancel(
        updated_at=at(4),
    )

    assert updated.status is ReceiptStatus.CANCELED
    assert updated.status.value == "canceled"
    assert updated.status.is_terminal is True
    assert updated.version == original.version + 1
    assert original is not updated


@pytest.mark.parametrize(
    "factory",
    [
        issued_receipt,
        delivered_receipt,
    ],
)
def test_void_accepts_issued_or_delivered(
    factory: Callable[[], Receipt],
) -> None:
    original = factory()

    updated = original.void(
        updated_at=at(4),
    )

    assert updated.status is ReceiptStatus.VOIDED
    assert updated.status.is_terminal is True
    assert updated.version == original.version + 1


def test_expire_transitions_issued_to_expired() -> None:
    original = issued_receipt()

    updated = original.expire(
        expired_at=at(4),
    )

    assert updated.status is ReceiptStatus.EXPIRED
    assert updated.status.is_terminal is True
    assert updated.expires_at == at(4)
    assert updated.updated_at == at(4)
    assert updated.version == original.version + 1


def test_expire_accepts_separate_update_timestamp() -> None:
    original = issued_receipt()

    updated = original.expire(
        expired_at=at(4),
        updated_at=at(5),
    )

    assert updated.expires_at == at(4)
    assert updated.updated_at == at(5)


@pytest.mark.parametrize(
    "factory",
    [
        issued_receipt,
        delivered_receipt,
    ],
)
def test_supersede_accepts_issued_or_delivered(
    factory: Callable[[], Receipt],
) -> None:
    original = factory()

    updated = original.supersede(
        updated_at=at(4),
    )

    assert updated.status is ReceiptStatus.SUPERSEDED
    assert updated.status.is_terminal is True
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    "factory",
    [
        draft_receipt,
        prepared_receipt,
        issued_receipt,
        delivered_receipt,
    ],
)
def test_update_metadata_accepts_non_terminal_states(
    factory: Callable[[], Receipt],
) -> None:
    original = factory()

    updated = original.update_metadata(
        {
            "channel": "mobile",
            "nested": {
                "values": [1, 2],
            },
        },
        updated_at=at(5),
    )

    assert updated.status is original.status
    assert updated.version == original.version + 1
    assert updated.updated_at == at(5)
    assert isinstance(
        updated.metadata,
        ReceiptMetadata,
    )

    payload = updated.canonical_dict()

    assert payload["metadata"]["channel"] == "mobile"
    assert payload["metadata"]["nested"]["values"] == [
        1,
        2,
    ]


def test_update_metadata_accepts_receipt_metadata() -> None:
    metadata = ReceiptMetadata.of(
        {
            "source": "operator",
        }
    )

    updated = issued_receipt().update_metadata(
        metadata,
        updated_at=at(5),
    )

    assert updated.metadata == metadata
    assert updated.status is ReceiptStatus.ISSUED


def test_update_metadata_payload_is_isolated() -> None:
    updated = issued_receipt().update_metadata(
        {
            "nested": {
                "values": [1, 2],
            },
        },
        updated_at=at(5),
    )

    payload = updated.canonical_dict()

    payload["metadata"]["nested"]["values"].append(
        3
    )

    fresh = updated.canonical_dict()

    assert fresh["metadata"]["nested"]["values"] == [
        1,
        2,
    ]


@pytest.mark.parametrize(
    ("factory", "method_name"),
    [
        (
            draft_receipt,
            "issue",
        ),
        (
            draft_receipt,
            "mark_delivered",
        ),
        (
            draft_receipt,
            "void",
        ),
        (
            draft_receipt,
            "expire",
        ),
        (
            draft_receipt,
            "supersede",
        ),
        (
            prepared_receipt,
            "prepare",
        ),
        (
            prepared_receipt,
            "mark_delivered",
        ),
        (
            prepared_receipt,
            "void",
        ),
        (
            prepared_receipt,
            "expire",
        ),
        (
            prepared_receipt,
            "supersede",
        ),
        (
            issued_receipt,
            "prepare",
        ),
        (
            issued_receipt,
            "issue",
        ),
        (
            issued_receipt,
            "cancel",
        ),
        (
            delivered_receipt,
            "prepare",
        ),
        (
            delivered_receipt,
            "issue",
        ),
        (
            delivered_receipt,
            "mark_delivered",
        ),
        (
            delivered_receipt,
            "cancel",
        ),
        (
            delivered_receipt,
            "expire",
        ),
    ],
)
def test_invalid_lifecycle_transitions_are_rejected(
    factory: Callable[[], Receipt],
    method_name: str,
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="status transition",
    ):
        method(
            updated_at=at(6),
        )


@pytest.mark.parametrize(
    "factory",
    [
        canceled_receipt,
        voided_receipt,
        expired_receipt,
        superseded_receipt,
    ],
)
def test_terminal_metadata_updates_are_rejected(
    factory: Callable[[], Receipt],
) -> None:
    aggregate = factory()

    assert aggregate.status.is_terminal is True

    with pytest.raises(
        ValueError,
        match="terminal receipt metadata",
    ):
        aggregate.update_metadata(
            {
                "changed": True,
            },
            updated_at=at(6),
        )


@pytest.mark.parametrize(
    ("factory", "method_name"),
    [
        (
            canceled_receipt,
            "prepare",
        ),
        (
            canceled_receipt,
            "issue",
        ),
        (
            canceled_receipt,
            "mark_delivered",
        ),
        (
            canceled_receipt,
            "cancel",
        ),
        (
            canceled_receipt,
            "void",
        ),
        (
            canceled_receipt,
            "expire",
        ),
        (
            canceled_receipt,
            "supersede",
        ),
        (
            voided_receipt,
            "prepare",
        ),
        (
            voided_receipt,
            "issue",
        ),
        (
            expired_receipt,
            "issue",
        ),
        (
            superseded_receipt,
            "mark_delivered",
        ),
    ],
)
def test_terminal_statuses_reject_further_transitions(
    factory: Callable[[], Receipt],
    method_name: str,
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="status transition",
    ):
        method(
            updated_at=at(7),
        )


@pytest.mark.parametrize(
    ("factory", "method_name", "kwargs"),
    [
        (
            prepared_receipt,
            "issue",
            {
                "issued_at": at(0),
            },
        ),
        (
            issued_receipt,
            "mark_delivered",
            {
                "delivered_at": at(1),
            },
        ),
        (
            issued_receipt,
            "expire",
            {
                "expired_at": at(1),
            },
        ),
        (
            issued_receipt,
            "void",
            {
                "updated_at": at(1),
            },
        ),
    ],
)
def test_transition_time_cannot_precede_current_update(
    factory: Callable[[], Receipt],
    method_name: str,
    kwargs: dict[str, datetime],
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="must not precede",
    ):
        method(**kwargs)


@pytest.mark.parametrize(
    ("factory", "method_name", "kwargs"),
    [
        (
            draft_receipt,
            "prepare",
            {
                "updated_at": datetime(
                    2026,
                    8,
                    5,
                    1,
                    0,
                ),
            },
        ),
        (
            prepared_receipt,
            "issue",
            {
                "issued_at": datetime(
                    2026,
                    8,
                    5,
                    2,
                    0,
                ),
            },
        ),
        (
            issued_receipt,
            "mark_delivered",
            {
                "delivered_at": datetime(
                    2026,
                    8,
                    5,
                    3,
                    0,
                ),
            },
        ),
    ],
)
def test_lifecycle_rejects_naive_datetimes(
    factory: Callable[[], Receipt],
    method_name: str,
    kwargs: dict[str, datetime],
) -> None:
    aggregate = factory()
    method = getattr(
        aggregate,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        method(**kwargs)


def test_lifecycle_normalizes_datetime_to_utc() -> None:
    plus_ten = timezone(
        timedelta(hours=10)
    )

    local_time = datetime(
        2026,
        8,
        5,
        11,
        0,
        tzinfo=plus_ten,
    )

    updated = draft_receipt().prepare(
        updated_at=local_time,
    )

    assert updated.updated_at == at(1)
    assert updated.updated_at.tzinfo is timezone.utc


def test_version_increments_once_per_transition() -> None:
    draft = draft_receipt()
    prepared = draft.prepare(
        updated_at=at(1),
    )
    issued = prepared.issue(
        issued_at=at(2),
    )
    delivered = issued.mark_delivered(
        delivered_at=at(3),
    )
    superseded = delivered.supersede(
        updated_at=at(4),
    )

    assert [
        draft.version,
        prepared.version,
        issued.version,
        delivered.version,
        superseded.version,
    ] == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_transition_preserves_receipt_identity() -> None:
    original = draft_receipt(
        receipt_id="receipt-identity-001",
    )

    updated = original.prepare(
        updated_at=at(1),
    )

    assert updated.receipt_id == original.receipt_id
    assert updated.receipt_type is original.receipt_type
    assert updated.currency_code == original.currency_code
    assert updated.created_at == original.created_at


def test_transition_does_not_mutate_original() -> None:
    original = draft_receipt()
    original_payload = original.canonical_dict()

    updated = original.prepare(
        updated_at=at(1),
    )

    assert original.status is ReceiptStatus.DRAFT
    assert original.version == 1
    assert original.canonical_dict() == original_payload

    assert updated.status is ReceiptStatus.PREPARED
    assert updated.version == 2


def test_receipt_remains_immutable_after_lifecycle_support() -> None:
    aggregate = issued_receipt()

    with pytest.raises(FrozenInstanceError):
        aggregate.status = ReceiptStatus.DELIVERED


@pytest.mark.parametrize(
    "factory",
    [
        prepared_receipt,
        issued_receipt,
        delivered_receipt,
        canceled_receipt,
        voided_receipt,
        expired_receipt,
        superseded_receipt,
    ],
)
def test_lifecycle_serialization_is_deterministic(
    factory: Callable[[], Receipt],
) -> None:
    aggregate = factory()

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first == second


@pytest.mark.parametrize(
    "factory",
    [
        prepared_receipt,
        issued_receipt,
        delivered_receipt,
        canceled_receipt,
        voided_receipt,
        expired_receipt,
        superseded_receipt,
    ],
)
def test_lifecycle_serialization_is_fresh(
    factory: Callable[[], Receipt],
) -> None:
    aggregate = factory()

    first = aggregate.canonical_dict()
    second = aggregate.canonical_dict()

    assert first is not second


def test_canceled_status_serialization() -> None:
    aggregate = canceled_receipt()

    payload = aggregate.canonical_dict()

    assert payload["status"] == "canceled"
    assert payload["version"] == 2


def test_issued_timestamp_serialization() -> None:
    payload = issued_receipt().canonical_dict()

    assert payload["issued_at"] == (
        "2026-08-05T02:00:00+00:00"
    )


def test_delivered_timestamp_serialization() -> None:
    payload = delivered_receipt().canonical_dict()

    assert payload["delivered_at"] == (
        "2026-08-05T03:00:00+00:00"
    )


def test_expired_timestamp_serialization() -> None:
    payload = expired_receipt().canonical_dict()

    assert payload["expires_at"] == (
        "2026-08-05T03:00:00+00:00"
    )


def test_transition_metadata_serialization_is_isolated() -> None:
    aggregate = issued_receipt().update_metadata(
        {
            "nested": {
                "values": [1, 2],
            },
        },
        updated_at=at(5),
    )

    payload = aggregate.canonical_dict()

    payload["metadata"]["nested"]["values"].append(
        3
    )

    fresh = aggregate.canonical_dict()

    assert fresh["metadata"]["nested"]["values"] == [
        1,
        2,
    ]


def test_lifecycle_methods_add_no_execution_authority() -> None:
    forbidden = {
        "execute_payment",
        "execute_transfer",
        "settle",
        "debit_wallet",
        "credit_wallet",
        "post_ledger",
        "submit_provider",
        "reconcile",
        "persist",
        "save",
        "deliver_external",
        "sign",
        "verify_external",
    }

    names = {
        name
        for name in dir(Receipt)
        if not name.startswith("__")
    }

    assert forbidden.isdisjoint(names)


def test_lifecycle_module_adds_no_repository_authority() -> None:
    source_names = {
        name.lower()
        for name in dir(receipt)
    }

    forbidden = {
        "receiptrepository",
        "sqlitereceiptrepository",
        "postgresreceiptrepository",
        "receiptpersistence",
        "receiptdeliveryservice",
        "receiptsigningservice",
        "receiptexternalverifier",
    }

    assert forbidden.isdisjoint(source_names)
