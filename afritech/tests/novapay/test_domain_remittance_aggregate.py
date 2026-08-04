from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.remittance import (
    Remittance,
    RemittanceDirection,
    RemittanceId,
    RemittanceMetadata,
    RemittancePriority,
    RemittancePurpose,
    RemittanceReference,
    RemittanceStatus,
    RemittanceType,
)
from afritech.novapay.domain.transfer import (
    TransferAccountReference,
    TransferPartyReference,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    13,
    0,
    tzinfo=timezone.utc,
)

UPDATED_AT = datetime(
    2026,
    8,
    3,
    13,
    5,
    tzinfo=timezone.utc,
)


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
            value = attempt()
        except (TypeError, ValueError):
            continue

        if isinstance(value, Money):
            return value

    raise AssertionError(
        f"unable to construct Money for {amount} {code}"
    )


def sender() -> TransferPartyReference:
    return TransferPartyReference(
        party_id="sender-001",
        party_type="customer",
    )


def beneficiary() -> TransferPartyReference:
    return TransferPartyReference(
        party_id="beneficiary-001",
        party_type="beneficiary",
    )


def source_account(
    *,
    currency_code: str = "AUD",
) -> TransferAccountReference:
    return TransferAccountReference(
        account_id="wallet-aud",
        account_type="wallet",
        currency_code=currency_code,
    )


def destination_account(
    *,
    currency_code: str = "BIF",
) -> TransferAccountReference:
    return TransferAccountReference(
        account_id="wallet-bif",
        account_type="wallet",
        currency_code=currency_code,
    )


def remittance(
    *,
    remittance_id: object = "remittance-001",
    reference: object = "reference/AU-BI/001",
    status: object = "draft",
    remittance_type: object = "international",
    direction: object = "outbound",
    purpose: object = "family_support",
    priority: object = "normal",
    sender_value: TransferPartyReference | None = None,
    beneficiary_value: TransferPartyReference | None = None,
    source_account_value: TransferAccountReference | None = None,
    destination_account_value: TransferAccountReference | None = None,
    source_amount: Money | None = None,
    destination_amount: Money | None = None,
    metadata: object = None,
    created_at: datetime = CREATED_AT,
    updated_at: datetime | None = UPDATED_AT,
    version: int = 1,
) -> Remittance:
    return Remittance.create(
        remittance_id=remittance_id,
        reference=reference,
        status=status,
        remittance_type=remittance_type,
        direction=direction,
        purpose=purpose,
        priority=priority,
        sender=(
            sender_value
            if sender_value is not None
            else sender()
        ),
        beneficiary=(
            beneficiary_value
            if beneficiary_value is not None
            else beneficiary()
        ),
        source_account=(
            source_account_value
            if source_account_value is not None
            else source_account()
        ),
        destination_account=(
            destination_account_value
            if destination_account_value is not None
            else destination_account()
        ),
        source_amount=(
            source_amount
            if source_amount is not None
            else money("100.00", "AUD")
        ),
        destination_amount=(
            destination_amount
            if destination_amount is not None
            else money("185000.00", "BIF")
        ),
        metadata=(
            metadata
            if metadata is not None
            else {
                "channel": "mobile",
                "corridor": "AU-BI",
            }
        ),
        created_at=created_at,
        updated_at=updated_at,
        version=version,
    )


def test_remittance_construction() -> None:
    value = remittance()

    assert value.remittance_id == RemittanceId.of(
        "remittance-001"
    )
    assert value.reference == RemittanceReference.of(
        "reference/AU-BI/001"
    )
    assert value.status is RemittanceStatus.DRAFT
    assert value.remittance_type is (
        RemittanceType.INTERNATIONAL
    )
    assert value.direction is RemittanceDirection.OUTBOUND
    assert value.purpose is (
        RemittancePurpose.FAMILY_SUPPORT
    )
    assert value.priority is RemittancePriority.NORMAL
    assert value.source_currency_code == "AUD"
    assert value.destination_currency_code == "BIF"
    assert value.created_at == CREATED_AT
    assert value.updated_at == UPDATED_AT
    assert value.version == 1


def test_remittance_factory_defaults_updated_at() -> None:
    value = remittance(
        updated_at=None,
    )

    assert value.updated_at == value.created_at


def test_remittance_factory_normalizes_primitives() -> None:
    value = remittance(
        remittance_id="remittance-002",
        reference="reference/AU-BI/002",
        status="in progress",
        remittance_type="cross-border",
        direction="send",
        purpose="family",
        priority="express",
    )

    assert value.remittance_id.value == "remittance-002"
    assert value.reference.value == (
        "reference/AU-BI/002"
    )
    assert value.status is RemittanceStatus.PROCESSING
    assert value.remittance_type is (
        RemittanceType.INTERNATIONAL
    )
    assert value.direction is RemittanceDirection.OUTBOUND
    assert value.purpose is (
        RemittancePurpose.FAMILY_SUPPORT
    )
    assert value.priority is RemittancePriority.URGENT


def test_remittance_preserves_identifier_instances() -> None:
    remittance_id = RemittanceId.of("remittance-001")
    reference = RemittanceReference.of(
        "reference/AU-BI/001"
    )

    value = remittance(
        remittance_id=remittance_id,
        reference=reference,
    )

    assert value.remittance_id is remittance_id
    assert value.reference is reference


def test_remittance_preserves_party_references() -> None:
    sender_value = sender()
    beneficiary_value = beneficiary()

    value = remittance(
        sender_value=sender_value,
        beneficiary_value=beneficiary_value,
    )

    assert value.sender is sender_value
    assert value.beneficiary is beneficiary_value


def test_remittance_preserves_account_references() -> None:
    source_value = source_account()
    destination_value = destination_account()

    value = remittance(
        source_account_value=source_value,
        destination_account_value=destination_value,
    )

    assert value.source_account is source_value
    assert value.destination_account is destination_value


def test_remittance_preserves_money_instances() -> None:
    source_value = money("100.00", "AUD")
    destination_value = money("185000.00", "BIF")

    value = remittance(
        source_amount=source_value,
        destination_amount=destination_value,
    )

    assert value.source_amount is source_value
    assert value.destination_amount is destination_value


def test_remittance_metadata_normalization() -> None:
    value = remittance(
        metadata={
            "Channel": "mobile",
            "Risk Level": 2,
        }
    )

    assert isinstance(
        value.metadata,
        RemittanceMetadata,
    )
    assert value.metadata.values == {
        "channel": "mobile",
        "risk_level": 2,
    }


def test_remittance_metadata_preserves_instance() -> None:
    metadata = RemittanceMetadata.of(
        {
            "channel": "mobile",
        }
    )

    value = remittance(
        metadata=metadata,
    )

    assert value.metadata is metadata


def test_remittance_datetime_normalizes_to_utc() -> None:
    offset = timezone(timedelta(hours=10))

    created_at = datetime(
        2026,
        8,
        3,
        23,
        0,
        tzinfo=offset,
    )
    updated_at = datetime(
        2026,
        8,
        3,
        23,
        5,
        tzinfo=offset,
    )

    value = remittance(
        created_at=created_at,
        updated_at=updated_at,
    )

    assert value.created_at == CREATED_AT
    assert value.updated_at == UPDATED_AT
    assert value.created_at.tzinfo is timezone.utc
    assert value.updated_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "status",
    [
        RemittanceStatus.COMPLETED,
        RemittanceStatus.FAILED,
        RemittanceStatus.CANCELLED,
        RemittanceStatus.EXPIRED,
        RemittanceStatus.REVERSED,
    ],
)
def test_terminal_status_classification(
    status: RemittanceStatus,
) -> None:
    assert remittance(status=status).is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        RemittanceStatus.DRAFT,
        RemittanceStatus.VALIDATED,
        RemittanceStatus.AUTHORIZED,
        RemittanceStatus.SUBMITTED,
        RemittanceStatus.PROCESSING,
    ],
)
def test_non_terminal_status_classification(
    status: RemittanceStatus,
) -> None:
    assert remittance(status=status).is_terminal is False


def test_cross_currency_classification() -> None:
    assert remittance().is_cross_currency is True


def test_same_currency_classification() -> None:
    value = remittance(
        destination_account_value=destination_account(
            currency_code="AUD",
        ),
        destination_amount=money(
            "100.00",
            "AUD",
        ),
    )

    assert value.is_cross_currency is False


def test_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(Remittance)
    } == {
        "remittance_id",
        "reference",
        "status",
        "remittance_type",
        "direction",
        "purpose",
        "priority",
        "sender",
        "beneficiary",
        "source_account",
        "destination_account",
        "source_amount",
        "destination_amount",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_remittance_is_immutable() -> None:
    value = remittance()

    with pytest.raises(FrozenInstanceError):
        value.status = RemittanceStatus.COMPLETED  # type: ignore[misc]


def test_remittance_canonical_dict() -> None:
    payload = remittance().canonical_dict()

    assert list(payload) == [
        "remittance_id",
        "reference",
        "status",
        "remittance_type",
        "direction",
        "purpose",
        "priority",
        "sender",
        "beneficiary",
        "source_account",
        "destination_account",
        "source_amount",
        "destination_amount",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["remittance_id"] == "remittance-001"
    assert payload["reference"] == (
        "reference/AU-BI/001"
    )
    assert payload["status"] == "draft"
    assert payload["remittance_type"] == "international"
    assert payload["direction"] == "outbound"
    assert payload["purpose"] == "family_support"
    assert payload["priority"] == "normal"
    assert payload["sender"]["party_id"] == "sender-001"
    assert payload["beneficiary"]["party_id"] == (
        "beneficiary-001"
    )
    assert payload["source_account"]["currency_code"] == (
        "AUD"
    )
    assert payload["destination_account"][
        "currency_code"
    ] == "BIF"
    assert "AUD" in str(payload["source_amount"])
    assert "BIF" in str(payload["destination_amount"])
    assert payload["metadata"] == {
        "channel": "mobile",
        "corridor": "AU-BI",
    }
    assert payload["created_at"] == (
        "2026-08-03T13:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-03T13:05:00+00:00"
    )
    assert payload["version"] == 1


def test_canonical_dict_returns_fresh_payloads() -> None:
    value = remittance()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["sender"] is not second["sender"]
    assert first["beneficiary"] is not second["beneficiary"]
    assert (
        first["source_account"]
        is not second["source_account"]
    )
    assert (
        first["destination_account"]
        is not second["destination_account"]
    )
    assert (
        first["source_amount"]
        is not second["source_amount"]
    )
    assert (
        first["destination_amount"]
        is not second["destination_amount"]
    )
    assert first["metadata"] is not second["metadata"]


def test_sender_and_beneficiary_must_differ() -> None:
    sender_value = sender()

    with pytest.raises(
        ValueError,
        match="sender and beneficiary must be different",
    ):
        remittance(
            sender_value=sender_value,
            beneficiary_value=sender_value,
        )


def test_source_and_destination_accounts_must_differ() -> None:
    account = source_account()

    with pytest.raises(
        ValueError,
        match="source and destination accounts must be different",
    ):
        remittance(
            source_account_value=account,
            destination_account_value=account,
            destination_amount=money(
                "100.00",
                "AUD",
            ),
        )


def test_source_amount_currency_must_match_account() -> None:
    with pytest.raises(
        ValueError,
        match="source amount currency must match",
    ):
        remittance(
            source_amount=money(
                "100.00",
                "USD",
            ),
        )


def test_destination_amount_currency_must_match_account() -> None:
    with pytest.raises(
        ValueError,
        match="destination amount currency must match",
    ):
        remittance(
            destination_amount=money(
                "185000.00",
                "USD",
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sender_value", object()),
        ("beneficiary_value", object()),
    ],
)
def test_party_references_reject_wrong_type(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        field_name: value,
    }

    with pytest.raises(
        TypeError,
        match="must be TransferPartyReference",
    ):
        remittance(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("source_account_value", object()),
        ("destination_account_value", object()),
    ],
)
def test_account_references_reject_wrong_type(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        field_name: value,
    }

    with pytest.raises(
        TypeError,
        match="must be TransferAccountReference",
    ):
        remittance(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("source_amount", object()),
        ("destination_amount", object()),
    ],
)
def test_amounts_reject_non_money(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        field_name: value,
    }

    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        remittance(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
    ],
)
def test_datetime_fields_reject_naive_values(
    field_name: str,
) -> None:
    kwargs = {
        field_name: datetime(
            2026,
            8,
            3,
            13,
            0,
        ),
    }

    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        remittance(**kwargs)


def test_updated_at_must_not_precede_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        remittance(
            updated_at=(
                CREATED_AT
                - timedelta(seconds=1)
            ),
        )


def test_same_timestamp_is_allowed() -> None:
    value = remittance(
        updated_at=CREATED_AT,
    )

    assert value.created_at == value.updated_at


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_version_rejects_non_positive_values(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        remittance(version=value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        1.5,
        "1",
        None,
    ],
)
def test_version_rejects_non_integer_values(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        remittance(
            version=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("remittance_id", ""),
        ("reference", ""),
        ("status", "unknown"),
        ("remittance_type", "unknown"),
        ("direction", "unknown"),
        ("purpose", "unknown"),
        ("priority", "unknown"),
    ],
)
def test_factory_rejects_invalid_normalized_values(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        field_name: value,
    }

    with pytest.raises((TypeError, ValueError)):
        remittance(**kwargs)


def test_sensitive_metadata_rejection() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        remittance(
            metadata={
                "authorization": "secret",
            }
        )


def test_aggregate_has_lifecycle_methods() -> None:
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
        "update_reference",
        "update_priority",
        "update_metadata",
    ):
        assert hasattr(Remittance, method_name)
        assert callable(getattr(Remittance, method_name))


def test_aggregate_has_no_runtime_authority() -> None:
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
        "convert",
        "lock_rate",
        "collect",
        "save",
        "persist",
        "repository",
        "database",
    ):
        assert forbidden not in names


def test_aggregate_fields_have_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(Remittance)
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "provider_client",
        "settlement_engine",
        "fx_engine",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names


def test_remittance_aggregate_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    from afritech.novapay.domain.remittance import Remittance

    assert domain.Remittance is Remittance
    assert novapay.Remittance is Remittance
    assert "Remittance" in domain.__all__
    assert "Remittance" in novapay.__all__
