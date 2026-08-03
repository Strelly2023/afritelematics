from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.transfer import (
    Transfer,
    TransferPriority,
    TransferStatus,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    9,
    0,
    tzinfo=timezone.utc,
)


def at(minutes: int) -> datetime:
    return CREATED_AT + timedelta(minutes=minutes)


def currency(code: str) -> Currency:
    parse = getattr(Currency, "parse", None)

    if callable(parse):
        try:
            value = parse(code)
        except (TypeError, ValueError):
            pass
        else:
            if isinstance(value, Currency):
                return value

    for attempt in (
        lambda: Currency(code),
        lambda: Currency(code=code),
    ):
        try:
            value = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(value, Currency):
            return value

    raise AssertionError(
        f"unable to construct Currency for {code}"
    )


def money(amount: str, code: str) -> Money:
    amount_value = Decimal(amount)
    currency_value = currency(code)

    factory = getattr(Money, "of", None)
    attempts = []

    if callable(factory):
        attempts.extend(
            (
                lambda: factory(
                    amount_value,
                    currency_value,
                ),
                lambda: factory(
                    amount=amount_value,
                    currency=currency_value,
                ),
            )
        )

    attempts.extend(
        (
            lambda: Money(
                amount=amount_value,
                currency=currency_value,
            ),
            lambda: Money(
                amount_value,
                currency_value,
            ),
        )
    )

    for attempt in attempts:
        try:
            value = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(value, Money):
            return value

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def transfer(
    *,
    transfer_id: str = "transfer-lifecycle-001",
    status: object = TransferStatus.DRAFT,
    priority: object = TransferPriority.NORMAL,
    metadata: object = None,
) -> Transfer:
    return Transfer.create(
        transfer_id=transfer_id,
        reference=f"reference-{transfer_id}",
        status=status,
        transfer_type="international",
        direction="outbound",
        purpose="family_support",
        priority=priority,
        sender={
            "party_id": "sender-001",
            "party_type": "customer",
        },
        beneficiary={
            "party_id": "beneficiary-001",
            "party_type": "beneficiary",
        },
        source_account={
            "account_id": "wallet-aud",
            "account_type": "wallet",
            "currency_code": "AUD",
        },
        destination_account={
            "account_id": "wallet-usd",
            "account_type": "wallet",
            "currency_code": "USD",
        },
        source_amount=money("100.00", "AUD"),
        destination_amount=money("65.00", "USD"),
        metadata=(
            metadata
            if metadata is not None
            else {"channel": "mobile"}
        ),
        created_at=CREATED_AT,
    )


def validated_transfer() -> Transfer:
    return transfer().validate(
        occurred_at=at(1),
        metadata={"validation_state": "passed"},
    )


def authorized_transfer() -> Transfer:
    return validated_transfer().authorize(
        occurred_at=at(2),
        metadata={"approval_state": "recorded"},
    )


def submitted_transfer() -> Transfer:
    return authorized_transfer().submit(
        occurred_at=at(3),
        metadata={"submission_state": "recorded"},
    )


def processing_transfer() -> Transfer:
    return submitted_transfer().mark_processing(
        occurred_at=at(4),
        metadata={"processing_state": "active"},
    )


def completed_transfer() -> Transfer:
    return processing_transfer().complete(
        occurred_at=at(5),
        metadata={"completion_state": "recorded"},
    )


def test_draft_to_validated() -> None:
    original = transfer()
    updated = original.validate(
        occurred_at=at(1),
        metadata={"validation_state": "passed"},
    )

    assert updated.status is TransferStatus.VALIDATED
    assert updated.version == 2
    assert updated.updated_at == at(1)
    assert updated.metadata.values[
        "validation_state"
    ] == "passed"

    assert original.status is TransferStatus.DRAFT
    assert original.version == 1


def test_validated_to_authorized() -> None:
    original = validated_transfer()
    updated = original.authorize(
        occurred_at=at(2),
        metadata={"approval_state": "recorded"},
    )

    assert updated.status is TransferStatus.AUTHORIZED
    assert updated.version == 3
    assert updated.updated_at == at(2)


def test_authorized_to_submitted() -> None:
    original = authorized_transfer()
    updated = original.submit(
        occurred_at=at(3),
        metadata={"submission_state": "recorded"},
    )

    assert updated.status is TransferStatus.SUBMITTED
    assert updated.version == 4
    assert updated.updated_at == at(3)


def test_submitted_to_processing() -> None:
    original = submitted_transfer()
    updated = original.mark_processing(
        occurred_at=at(4),
    )

    assert updated.status is TransferStatus.PROCESSING
    assert updated.version == 5


def test_processing_to_completed() -> None:
    original = processing_transfer()
    updated = original.complete(
        occurred_at=at(5),
        metadata={"completion_state": "recorded"},
    )

    assert updated.status is TransferStatus.COMPLETED
    assert updated.version == 6
    assert updated.is_terminal is True


def test_completed_to_reversed() -> None:
    original = completed_transfer()
    updated = original.reverse(
        occurred_at=at(6),
        metadata={"reversal_state": "recorded"},
    )

    assert updated.status is TransferStatus.REVERSED
    assert updated.version == 7
    assert updated.is_terminal is True


@pytest.mark.parametrize(
    "factory",
    [
        lambda: transfer(
            transfer_id="cancel-draft"
        ),
        lambda: validated_transfer(),
        lambda: authorized_transfer(),
        lambda: submitted_transfer(),
        lambda: processing_transfer(),
    ],
)
def test_allowed_cancellation_paths(
    factory: object,
) -> None:
    original = factory()  # type: ignore[operator]
    updated = original.cancel(
        occurred_at=original.updated_at
        + timedelta(minutes=1),
        metadata={"cancellation_state": "recorded"},
    )

    assert updated.status is TransferStatus.CANCELLED
    assert updated.is_terminal is True
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    "factory",
    [
        lambda: transfer(
            transfer_id="expire-draft"
        ),
        lambda: validated_transfer(),
        lambda: authorized_transfer(),
        lambda: submitted_transfer(),
    ],
)
def test_allowed_expiry_paths(
    factory: object,
) -> None:
    original = factory()  # type: ignore[operator]
    updated = original.expire(
        occurred_at=original.updated_at
        + timedelta(minutes=1),
        metadata={"expiry_state": "recorded"},
    )

    assert updated.status is TransferStatus.EXPIRED
    assert updated.is_terminal is True
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    "factory",
    [
        submitted_transfer,
        processing_transfer,
    ],
)
def test_allowed_failure_paths(
    factory: object,
) -> None:
    original = factory()  # type: ignore[operator]
    updated = original.fail(
        occurred_at=original.updated_at
        + timedelta(minutes=1),
        metadata={"failure_state": "recorded"},
    )

    assert updated.status is TransferStatus.FAILED
    assert updated.is_terminal is True
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    ("factory", "method_name"),
    [
        (transfer, "authorize"),
        (transfer, "submit"),
        (transfer, "mark_processing"),
        (transfer, "complete"),
        (transfer, "fail"),
        (transfer, "reverse"),
        (validated_transfer, "validate"),
        (validated_transfer, "submit"),
        (validated_transfer, "complete"),
        (authorized_transfer, "validate"),
        (authorized_transfer, "complete"),
        (submitted_transfer, "authorize"),
        (submitted_transfer, "complete"),
        (processing_transfer, "submit"),
        (processing_transfer, "reverse"),
        (completed_transfer, "complete"),
    ],
)
def test_invalid_transition_matrix(
    factory: object,
    method_name: str,
) -> None:
    original = factory()  # type: ignore[operator]
    method = getattr(original, method_name)

    with pytest.raises(
        ValueError,
        match="invalid transfer status transition",
    ):
        method(
            occurred_at=original.updated_at
            + timedelta(minutes=1)
        )


@pytest.mark.parametrize(
    "terminal",
    [
        lambda: transfer(
            transfer_id="terminal-failed"
        )
        .validate(occurred_at=at(1))
        .authorize(occurred_at=at(2))
        .submit(occurred_at=at(3))
        .fail(occurred_at=at(4)),
        lambda: transfer(
            transfer_id="terminal-cancelled"
        ).cancel(occurred_at=at(1)),
        lambda: transfer(
            transfer_id="terminal-expired"
        ).expire(occurred_at=at(1)),
        lambda: completed_transfer().reverse(
            occurred_at=at(6)
        ),
    ],
)
def test_terminal_states_reject_transitions(
    terminal: object,
) -> None:
    value = terminal()  # type: ignore[operator]

    for method_name in (
        "validate",
        "authorize",
        "submit",
        "mark_processing",
        "complete",
        "fail",
        "cancel",
        "expire",
        "reverse",
    ):
        method = getattr(value, method_name)

        with pytest.raises(
            ValueError,
            match="invalid transfer status transition",
        ):
            method(
                occurred_at=value.updated_at
                + timedelta(minutes=1)
            )


def test_update_reference_in_draft() -> None:
    original = transfer()
    updated = original.update_reference(
        "new-reference",
        occurred_at=at(1),
    )

    assert updated.reference.value == "new-reference"
    assert updated.version == 2
    assert original.reference.value != "new-reference"


@pytest.mark.parametrize(
    "factory",
    [
        validated_transfer,
        authorized_transfer,
        submitted_transfer,
        processing_transfer,
        completed_transfer,
    ],
)
def test_update_reference_rejected_after_draft(
    factory: object,
) -> None:
    value = factory()  # type: ignore[operator]

    with pytest.raises(
        ValueError,
        match="only be changed in draft",
    ):
        value.update_reference(
            "new-reference",
            occurred_at=value.updated_at
            + timedelta(minutes=1),
        )


def test_update_priority_non_terminal() -> None:
    original = validated_transfer()
    updated = original.update_priority(
        "urgent",
        occurred_at=at(2),
    )

    assert updated.priority is TransferPriority.URGENT
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    "terminal",
    [
        lambda: transfer(
            transfer_id="priority-cancelled"
        ).cancel(occurred_at=at(1)),
        lambda: transfer(
            transfer_id="priority-expired"
        ).expire(occurred_at=at(1)),
        completed_transfer,
    ],
)
def test_terminal_priority_update_rejected(
    terminal: object,
) -> None:
    value = terminal()  # type: ignore[operator]

    with pytest.raises(
        ValueError,
        match="terminal transfer priority",
    ):
        value.update_priority(
            "urgent",
            occurred_at=value.updated_at
            + timedelta(minutes=1),
        )


def test_update_metadata() -> None:
    original = authorized_transfer()
    updated = original.update_metadata(
        {
            "channel": "mobile",
            "review_state": "complete",
        },
        occurred_at=at(3),
    )

    assert updated.metadata.values[
        "review_state"
    ] == "complete"
    assert updated.version == original.version + 1


@pytest.mark.parametrize(
    "operation",
    [
        lambda value: value.update_reference(
            value.reference,
            occurred_at=at(1),
        ),
        lambda value: value.update_priority(
            value.priority,
            occurred_at=at(1),
        ),
        lambda value: value.update_metadata(
            value.metadata,
            occurred_at=at(1),
        ),
    ],
)
def test_noop_updates_rejected(
    operation: object,
) -> None:
    value = transfer()

    with pytest.raises(ValueError):
        operation(value)  # type: ignore[operator]


def test_backdated_status_transition_rejected() -> None:
    value = validated_transfer()

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        value.authorize(
            occurred_at=CREATED_AT,
        )


def test_backdated_reference_update_rejected() -> None:
    value = transfer().update_priority(
        "high",
        occurred_at=at(2),
    )

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        value.update_reference(
            "new-reference",
            occurred_at=at(1),
        )


def test_backdated_priority_update_rejected() -> None:
    value = validated_transfer()

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        value.update_priority(
            "urgent",
            occurred_at=CREATED_AT,
        )


def test_backdated_metadata_update_rejected() -> None:
    value = validated_transfer()

    with pytest.raises(
        ValueError,
        match="earlier than updated_at",
    ):
        value.update_metadata(
            {"state": "changed"},
            occurred_at=CREATED_AT,
        )


def test_same_timestamp_update_is_allowed() -> None:
    value = transfer()

    updated = value.update_priority(
        "high",
        occurred_at=CREATED_AT,
    )

    assert updated.updated_at == CREATED_AT
    assert updated.version == 2


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "authorization_token",
        "provider_authorization",
        "api_key",
        "password",
        "access_token",
    ],
)
def test_lifecycle_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        transfer().validate(
            occurred_at=at(1),
            metadata={key: "sensitive"},
        )


def test_lifecycle_preserves_identity_and_money() -> None:
    original = transfer()
    updated = (
        original
        .validate(occurred_at=at(1))
        .authorize(occurred_at=at(2))
        .submit(occurred_at=at(3))
        .mark_processing(occurred_at=at(4))
    )

    assert updated.transfer_id is original.transfer_id
    assert updated.reference is original.reference
    assert updated.sender is original.sender
    assert updated.beneficiary is original.beneficiary
    assert updated.source_account is original.source_account
    assert (
        updated.destination_account
        is original.destination_account
    )
    assert updated.source_amount is original.source_amount
    assert (
        updated.destination_amount
        is original.destination_amount
    )
    assert updated.created_at == original.created_at


def test_update_reference_preserves_other_fields() -> None:
    original = transfer()
    updated = original.update_reference(
        "changed-reference",
        occurred_at=at(1),
    )

    assert updated.status is original.status
    assert updated.priority is original.priority
    assert updated.metadata is original.metadata
    assert updated.source_amount is original.source_amount
    assert (
        updated.destination_amount
        is original.destination_amount
    )


def test_update_priority_preserves_other_fields() -> None:
    original = transfer()
    updated = original.update_priority(
        "urgent",
        occurred_at=at(1),
    )

    assert updated.reference is original.reference
    assert updated.status is original.status
    assert updated.metadata is original.metadata


def test_update_metadata_preserves_other_fields() -> None:
    original = transfer()
    updated = original.update_metadata(
        {"channel": "web"},
        occurred_at=at(1),
    )

    assert updated.reference is original.reference
    assert updated.priority is original.priority
    assert updated.status is original.status


def test_complete_lifecycle_exact_version_chain() -> None:
    value = transfer()
    assert value.version == 1

    value = value.update_reference(
        "updated-reference",
        occurred_at=at(1),
    )
    assert value.version == 2

    value = value.update_priority(
        "high",
        occurred_at=at(2),
    )
    assert value.version == 3

    value = value.update_metadata(
        {"channel": "mobile", "reviewed": True},
        occurred_at=at(3),
    )
    assert value.version == 4

    value = value.validate(occurred_at=at(4))
    assert value.version == 5

    value = value.authorize(occurred_at=at(5))
    assert value.version == 6

    value = value.submit(occurred_at=at(6))
    assert value.version == 7

    value = value.mark_processing(occurred_at=at(7))
    assert value.version == 8

    value = value.complete(occurred_at=at(8))
    assert value.version == 9

    value = value.reverse(occurred_at=at(9))
    assert value.version == 10


def test_lifecycle_returns_new_instances() -> None:
    draft = transfer()
    validated = draft.validate(
        occurred_at=at(1)
    )
    authorized = validated.authorize(
        occurred_at=at(2)
    )

    assert validated is not draft
    assert authorized is not validated
    assert authorized is not draft


def test_lifecycle_aggregate_remains_immutable() -> None:
    value = validated_transfer()

    with pytest.raises(FrozenInstanceError):
        value.status = TransferStatus.COMPLETED  # type: ignore[misc]


def test_lifecycle_methods_contain_no_runtime_authority() -> None:
    names = {
        name
        for name in dir(Transfer)
        if not name.startswith("__")
    }

    for forbidden in (
        "debit",
        "credit",
        "post",
        "post_entry",
        "settle",
        "execute",
        "send",
        "submit_to_provider",
        "request",
        "fetch",
        "connect",
        "lock_rate",
        "convert",
        "save",
        "persist",
        "repository",
        "database",
    ):
        assert forbidden not in names

    assert "submit" in names
    assert "complete" in names
    assert "reverse" in names


def test_transfer_lifecycle_is_exported_from_domain() -> None:
    import afritech.novapay.domain as domain

    assert domain.Transfer is Transfer
