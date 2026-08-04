from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.remittance import (
    Remittance,
    RemittanceMetadata,
    RemittancePriority,
    RemittanceReference,
    RemittanceStatus,
)
from afritech.novapay.domain.transfer import (
    TransferAccountReference,
    TransferPartyReference,
)


CREATED_AT = datetime(
    2026,
    8,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)


def at(minutes: int) -> datetime:
    return CREATED_AT + timedelta(minutes=minutes)


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

    for attempt in (
        lambda: Currency(code),
        lambda: Currency(code=code),
    ):
        try:
            result = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Currency):
            return result

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
            result = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(result, Money):
            return result

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def remittance(
    *,
    identifier: str = "remittance-001",
    status: object = RemittanceStatus.DRAFT,
    reference: object = "reference/AU-BI/001",
    priority: object = RemittancePriority.NORMAL,
    metadata: object = None,
    created_at: datetime = CREATED_AT,
    updated_at: datetime | None = None,
    version: int = 1,
) -> Remittance:
    return Remittance.create(
        remittance_id=identifier,
        reference=reference,
        status=status,
        remittance_type="international",
        direction="outbound",
        purpose="family_support",
        priority=priority,
        sender=TransferPartyReference(
            party_id=f"sender-{identifier}",
            party_type="customer",
        ),
        beneficiary=TransferPartyReference(
            party_id=f"beneficiary-{identifier}",
            party_type="beneficiary",
        ),
        source_account=TransferAccountReference(
            account_id=f"source-{identifier}",
            account_type="wallet",
            currency_code="AUD",
        ),
        destination_account=TransferAccountReference(
            account_id=f"destination-{identifier}",
            account_type="wallet",
            currency_code="BIF",
        ),
        source_amount=money("100.00", "AUD"),
        destination_amount=money("185000.00", "BIF"),
        metadata=(
            {"channel": "mobile"}
            if metadata is None
            else metadata
        ),
        created_at=created_at,
        updated_at=updated_at,
        version=version,
    )


def validated(value: Remittance) -> Remittance:
    return value.validate(
        occurred_at=value.updated_at + timedelta(minutes=1),
    )


def authorized(value: Remittance) -> Remittance:
    validated_value = validated(value)

    return validated_value.authorize(
        occurred_at=(
            validated_value.updated_at
            + timedelta(minutes=1)
        ),
    )


def submitted(value: Remittance) -> Remittance:
    authorized_value = authorized(value)

    return authorized_value.submit(
        occurred_at=(
            authorized_value.updated_at
            + timedelta(minutes=1)
        ),
    )


def processing(value: Remittance) -> Remittance:
    submitted_value = submitted(value)

    return submitted_value.mark_processing(
        occurred_at=(
            submitted_value.updated_at
            + timedelta(minutes=1)
        ),
    )


def completed(value: Remittance) -> Remittance:
    processing_value = processing(value)

    return processing_value.complete(
        occurred_at=(
            processing_value.updated_at
            + timedelta(minutes=1)
        ),
    )


def test_validate_transition() -> None:
    original = remittance()

    updated = original.validate(
        occurred_at=at(1),
        metadata={"validation_result": "approved"},
    )

    assert original.status is RemittanceStatus.DRAFT
    assert updated.status is RemittanceStatus.VALIDATED
    assert updated.updated_at == at(1)
    assert updated.version == 2
    assert updated.metadata.values == {
        "validation_result": "approved",
    }


def test_authorize_transition() -> None:
    original = remittance()
    value = original.validate(occurred_at=at(1))

    updated = value.authorize(
        occurred_at=at(2),
        metadata={"approval_state": "approved"},
    )

    assert updated.status is RemittanceStatus.AUTHORIZED
    assert updated.updated_at == at(2)
    assert updated.version == 3


def test_submit_transition() -> None:
    value = remittance().validate(
        occurred_at=at(1),
    ).authorize(
        occurred_at=at(2),
    )

    updated = value.submit(
        occurred_at=at(3),
        metadata={"submission_state": "accepted"},
    )

    assert updated.status is RemittanceStatus.SUBMITTED
    assert updated.version == 4


def test_mark_processing_transition() -> None:
    value = remittance().validate(
        occurred_at=at(1),
    ).authorize(
        occurred_at=at(2),
    ).submit(
        occurred_at=at(3),
    )

    updated = value.mark_processing(
        occurred_at=at(4),
        metadata={"processing_state": "active"},
    )

    assert updated.status is RemittanceStatus.PROCESSING
    assert updated.version == 5


def test_complete_transition() -> None:
    value = remittance().validate(
        occurred_at=at(1),
    ).authorize(
        occurred_at=at(2),
    ).submit(
        occurred_at=at(3),
    ).mark_processing(
        occurred_at=at(4),
    )

    updated = value.complete(
        occurred_at=at(5),
        metadata={"completion_state": "complete"},
    )

    assert updated.status is RemittanceStatus.COMPLETED
    assert updated.is_terminal is True
    assert updated.version == 6


@pytest.mark.parametrize(
    "source_status",
    [
        RemittanceStatus.SUBMITTED,
        RemittanceStatus.PROCESSING,
    ],
)
def test_fail_from_allowed_statuses(
    source_status: RemittanceStatus,
) -> None:
    if source_status is RemittanceStatus.SUBMITTED:
        value = submitted(remittance())
    else:
        value = processing(remittance())

    updated = value.fail(
        occurred_at=value.updated_at + timedelta(minutes=1),
        metadata={"failure_reason": "recipient_unavailable"},
    )

    assert updated.status is RemittanceStatus.FAILED
    assert updated.is_terminal is True
    assert updated.version == value.version + 1


@pytest.mark.parametrize(
    "source_status",
    [
        RemittanceStatus.DRAFT,
        RemittanceStatus.VALIDATED,
        RemittanceStatus.AUTHORIZED,
        RemittanceStatus.SUBMITTED,
    ],
)
def test_cancel_from_allowed_statuses(
    source_status: RemittanceStatus,
) -> None:
    value = remittance()

    if source_status is RemittanceStatus.VALIDATED:
        value = validated(value)
    elif source_status is RemittanceStatus.AUTHORIZED:
        value = authorized(value)
    elif source_status is RemittanceStatus.SUBMITTED:
        value = submitted(value)

    updated = value.cancel(
        occurred_at=value.updated_at + timedelta(minutes=1),
        metadata={"cancellation_reason": "customer_request"},
    )

    assert updated.status is RemittanceStatus.CANCELLED
    assert updated.is_terminal is True


@pytest.mark.parametrize(
    "source_status",
    [
        RemittanceStatus.DRAFT,
        RemittanceStatus.VALIDATED,
        RemittanceStatus.AUTHORIZED,
        RemittanceStatus.SUBMITTED,
    ],
)
def test_expire_from_allowed_statuses(
    source_status: RemittanceStatus,
) -> None:
    value = remittance()

    if source_status is RemittanceStatus.VALIDATED:
        value = validated(value)
    elif source_status is RemittanceStatus.AUTHORIZED:
        value = authorized(value)
    elif source_status is RemittanceStatus.SUBMITTED:
        value = submitted(value)

    updated = value.expire(
        occurred_at=value.updated_at + timedelta(minutes=1),
        metadata={"expiry_reason": "timeout"},
    )

    assert updated.status is RemittanceStatus.EXPIRED
    assert updated.is_terminal is True


def test_reverse_completed_remittance() -> None:
    value = completed(remittance())

    updated = value.reverse(
        occurred_at=value.updated_at + timedelta(minutes=1),
        metadata={"reversal_reason": "recipient_return"},
    )

    assert updated.status is RemittanceStatus.REVERSED
    assert updated.is_terminal is True
    assert updated.version == value.version + 1


@pytest.mark.parametrize(
    ("method_name", "source_status"),
    [
        ("validate", RemittanceStatus.VALIDATED),
        ("authorize", RemittanceStatus.DRAFT),
        ("submit", RemittanceStatus.VALIDATED),
        ("mark_processing", RemittanceStatus.AUTHORIZED),
        ("complete", RemittanceStatus.SUBMITTED),
        ("fail", RemittanceStatus.DRAFT),
        ("reverse", RemittanceStatus.PROCESSING),
    ],
)
def test_invalid_transition_matrix(
    method_name: str,
    source_status: RemittanceStatus,
) -> None:
    value = remittance(
        status=source_status,
    )

    method = getattr(value, method_name)

    with pytest.raises(ValueError):
        method(occurred_at=at(1))


@pytest.mark.parametrize(
    "terminal_status",
    [
        RemittanceStatus.COMPLETED,
        RemittanceStatus.FAILED,
        RemittanceStatus.CANCELLED,
        RemittanceStatus.EXPIRED,
        RemittanceStatus.REVERSED,
    ],
)
def test_terminal_states_reject_updates(
    terminal_status: RemittanceStatus,
) -> None:
    value = remittance(
        status=terminal_status,
    )

    with pytest.raises(
        ValueError,
        match="terminal remittance cannot be updated",
    ):
        value.update_priority(
            priority="urgent",
            occurred_at=at(1),
        )

    with pytest.raises(
        ValueError,
        match="terminal remittance cannot be updated",
    ):
        value.update_metadata(
            metadata={"state": "changed"},
            occurred_at=at(1),
        )


def test_update_reference_while_draft() -> None:
    original = remittance()

    updated = original.update_reference(
        reference="reference/AU-BI/002",
        occurred_at=at(1),
    )

    assert original.reference == RemittanceReference.of(
        "reference/AU-BI/001"
    )
    assert updated.reference == RemittanceReference.of(
        "reference/AU-BI/002"
    )
    assert updated.status is RemittanceStatus.DRAFT
    assert updated.version == 2


@pytest.mark.parametrize(
    "status",
    [
        RemittanceStatus.VALIDATED,
        RemittanceStatus.AUTHORIZED,
        RemittanceStatus.SUBMITTED,
        RemittanceStatus.PROCESSING,
    ],
)
def test_reference_update_is_draft_only(
    status: RemittanceStatus,
) -> None:
    value = remittance(status=status)

    with pytest.raises(
        ValueError,
        match="only be updated while draft",
    ):
        value.update_reference(
            reference="reference/changed",
            occurred_at=at(1),
        )


def test_update_priority() -> None:
    original = remittance()

    updated = original.update_priority(
        priority="urgent",
        occurred_at=at(1),
    )

    assert original.priority is RemittancePriority.NORMAL
    assert updated.priority is RemittancePriority.URGENT
    assert updated.version == 2


def test_update_metadata() -> None:
    original = remittance()

    updated = original.update_metadata(
        metadata={
            "channel": "mobile",
            "review_state": "complete",
        },
        occurred_at=at(1),
    )

    assert original.metadata.values == {
        "channel": "mobile",
    }
    assert updated.metadata.values == {
        "channel": "mobile",
        "review_state": "complete",
    }
    assert updated.version == 2


def test_same_timestamp_transition_is_allowed() -> None:
    value = remittance()

    updated = value.validate(
        occurred_at=value.updated_at,
    )

    assert updated.updated_at == value.updated_at
    assert updated.version == value.version + 1


def test_same_timestamp_update_is_allowed() -> None:
    value = remittance()

    updated = value.update_priority(
        priority="urgent",
        occurred_at=value.updated_at,
    )

    assert updated.updated_at == value.updated_at
    assert updated.version == value.version + 1


@pytest.mark.parametrize(
    "method_name",
    [
        "validate",
        "cancel",
        "expire",
    ],
)
def test_lifecycle_rejects_earlier_timestamp(
    method_name: str,
) -> None:
    value = remittance(
        updated_at=at(5),
    )

    method = getattr(value, method_name)

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        method(occurred_at=at(4))


@pytest.mark.parametrize(
    "method_name",
    [
        "update_reference",
        "update_priority",
        "update_metadata",
    ],
)
def test_updates_reject_earlier_timestamp(
    method_name: str,
) -> None:
    value = remittance(
        updated_at=at(5),
    )

    kwargs: dict[str, object] = {
        "occurred_at": at(4),
    }

    if method_name == "update_reference":
        kwargs["reference"] = "reference/changed"
    elif method_name == "update_priority":
        kwargs["priority"] = "urgent"
    else:
        kwargs["metadata"] = {
            "channel": "web",
        }

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        getattr(value, method_name)(**kwargs)


def test_noop_reference_update_rejected() -> None:
    value = remittance()

    with pytest.raises(
        ValueError,
        match="must change value",
    ):
        value.update_reference(
            reference=value.reference,
            occurred_at=at(1),
        )


def test_noop_priority_update_rejected() -> None:
    value = remittance()

    with pytest.raises(
        ValueError,
        match="must change value",
    ):
        value.update_priority(
            priority=value.priority,
            occurred_at=at(1),
        )


def test_noop_metadata_update_rejected() -> None:
    value = remittance()

    with pytest.raises(
        ValueError,
        match="must change value",
    ):
        value.update_metadata(
            metadata=value.metadata,
            occurred_at=at(1),
        )


@pytest.mark.parametrize(
    "method_name",
    [
        "validate",
        "authorize",
        "submit",
        "mark_processing",
        "complete",
        "fail",
        "cancel",
        "expire",
        "reverse",
    ],
)
def test_lifecycle_rejects_sensitive_metadata(
    method_name: str,
) -> None:
    value = remittance()

    if method_name == "authorize":
        value = validated(value)
    elif method_name == "submit":
        value = authorized(value)
    elif method_name == "mark_processing":
        value = submitted(value)
    elif method_name in {"complete", "fail"}:
        value = processing(value)
    elif method_name == "reverse":
        value = completed(value)

    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        getattr(value, method_name)(
            occurred_at=(
                value.updated_at
                + timedelta(minutes=1)
            ),
            metadata={
                "authorization": "secret",
            },
        )


def test_metadata_update_rejects_sensitive_metadata() -> None:
    value = remittance()

    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        value.update_metadata(
            metadata={
                "api_key": "secret",
            },
            occurred_at=at(1),
        )


def test_lifecycle_preserves_identity_and_money() -> None:
    original = remittance()
    updated = original.validate(
        occurred_at=at(1),
    )

    assert updated.remittance_id is original.remittance_id
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


def test_update_preserves_identity_and_money() -> None:
    original = remittance()
    updated = original.update_priority(
        priority="urgent",
        occurred_at=at(1),
    )

    assert updated.remittance_id is original.remittance_id
    assert updated.sender is original.sender
    assert updated.beneficiary is original.beneficiary
    assert updated.source_amount is original.source_amount
    assert (
        updated.destination_amount
        is original.destination_amount
    )


def test_exact_successful_lifecycle_version_chain() -> None:
    draft_value = remittance()
    reference_value = draft_value.update_reference(
        reference="reference/AU-BI/002",
        occurred_at=at(1),
    )
    priority_value = reference_value.update_priority(
        priority="urgent",
        occurred_at=at(2),
    )
    metadata_value = priority_value.update_metadata(
        metadata={
            "channel": "mobile",
            "review_state": "complete",
        },
        occurred_at=at(3),
    )
    validated_value = metadata_value.validate(
        occurred_at=at(4),
    )
    authorized_value = validated_value.authorize(
        occurred_at=at(5),
    )
    submitted_value = authorized_value.submit(
        occurred_at=at(6),
    )
    processing_value = submitted_value.mark_processing(
        occurred_at=at(7),
    )
    completed_value = processing_value.complete(
        occurred_at=at(8),
    )
    reversed_value = completed_value.reverse(
        occurred_at=at(9),
    )

    assert [
        draft_value.version,
        reference_value.version,
        priority_value.version,
        metadata_value.version,
        validated_value.version,
        authorized_value.version,
        submitted_value.version,
        processing_value.version,
        completed_value.version,
        reversed_value.version,
    ] == list(range(1, 11))


def test_lifecycle_results_are_immutable() -> None:
    updated = remittance().validate(
        occurred_at=at(1),
    )

    with pytest.raises(FrozenInstanceError):
        updated.status = RemittanceStatus.COMPLETED  # type: ignore[misc]


def test_lifecycle_metadata_is_remittance_metadata() -> None:
    updated = remittance().validate(
        occurred_at=at(1),
        metadata={
            "validation_result": "approved",
        },
    )

    assert isinstance(
        updated.metadata,
        RemittanceMetadata,
    )


def test_lifecycle_domain_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    from afritech.novapay.domain.remittance import Remittance

    assert domain.Remittance is Remittance
    assert novapay.Remittance is Remittance
    assert "Remittance" in domain.__all__
    assert "Remittance" in novapay.__all__


def test_lifecycle_has_no_runtime_execution_authority() -> None:
    names = {
        name
        for name in dir(Remittance)
        if not name.startswith("__")
    }

    for forbidden in (
        "authorize_funds",
        "reserve",
        "reserve_funds",
        "debit",
        "credit",
        "post",
        "post_entry",
        "settle",
        "execute",
        "submit_to_provider",
        "send",
        "route",
        "select_provider",
        "convert",
        "lock_rate",
        "collect",
        "save",
        "persist",
        "repository",
        "database",
    ):
        assert forbidden not in names
