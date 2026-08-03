from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.transfer import (
    Transfer,
    TransferAccountReference,
    TransferDirection,
    TransferId,
    TransferMetadata,
    TransferPartyReference,
    TransferPriority,
    TransferPurpose,
    TransferReference,
    TransferStatus,
    TransferType,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    5,
    0,
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

    attempts = (
        lambda: Currency(code),
        lambda: Currency(code=code),
    )

    for attempt in attempts:
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
                lambda: factory(
                    amount,
                    code,
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
    transfer_id: object = "transfer-001",
    reference: object = "reference-001",
    status: object = "draft",
    transfer_type: object = "international",
    direction: object = "outbound",
    purpose: object = "family_support",
    priority: object = "high",
    sender: object | None = None,
    beneficiary: object | None = None,
    source_account: object | None = None,
    destination_account: object | None = None,
    source_amount: Money | None = None,
    destination_amount: Money | None = None,
    metadata: object = None,
    created_at: datetime = CREATED_AT,
) -> Transfer:
    return Transfer.create(
        transfer_id=transfer_id,
        reference=reference,
        status=status,
        transfer_type=transfer_type,
        direction=direction,
        purpose=purpose,
        priority=priority,
        sender=sender
        or {
            "party_id": "sender-001",
            "party_type": "customer",
            "display_name": "Sender",
        },
        beneficiary=beneficiary
        or {
            "party_id": "beneficiary-001",
            "party_type": "beneficiary",
            "display_name": "Beneficiary",
        },
        source_account=source_account
        or {
            "account_id": "wallet-aud",
            "account_type": "wallet",
            "currency_code": "AUD",
            "institution_reference": "novapay-au",
        },
        destination_account=destination_account
        or {
            "account_id": "wallet-usd",
            "account_type": "wallet",
            "currency_code": "USD",
            "institution_reference": "novapay-us",
        },
        source_amount=source_amount
        or money("100.00", "AUD"),
        destination_amount=destination_amount
        or money("65.00", "USD"),
        metadata=metadata
        if metadata is not None
        else {
            "channel": "mobile",
            "corridor": "AU-US",
        },
        created_at=created_at,
    )


def test_create_transfer() -> None:
    value = transfer()

    assert value.transfer_id == TransferId(
        "transfer-001"
    )
    assert value.reference == TransferReference(
        "reference-001"
    )
    assert value.status is TransferStatus.DRAFT
    assert value.transfer_type is (
        TransferType.INTERNATIONAL
    )
    assert value.direction is (
        TransferDirection.OUTBOUND
    )
    assert value.purpose is (
        TransferPurpose.FAMILY_SUPPORT
    )
    assert value.priority is TransferPriority.HIGH
    assert value.version == 1
    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_factory_normalizes_all_classifications() -> None:
    value = transfer(
        status=" DRAFT ",
        transfer_type="business-payment",
        direction=" OUTBOUND ",
        purpose="goods and services",
        priority=" urgent ",
    )

    assert value.status is TransferStatus.DRAFT
    assert value.transfer_type is (
        TransferType.BUSINESS_PAYMENT
    )
    assert value.direction is (
        TransferDirection.OUTBOUND
    )
    assert value.purpose is (
        TransferPurpose.GOODS_AND_SERVICES
    )
    assert value.priority is TransferPriority.URGENT


def test_factory_normalizes_identifiers() -> None:
    value = transfer(
        transfer_id=" transfer-001 ",
        reference=" reference-001 ",
    )

    assert value.transfer_id.value == "transfer-001"
    assert value.reference.value == "reference-001"


def test_factory_normalizes_party_references() -> None:
    value = transfer(
        sender={
            "party_id": " sender-001 ",
            "party_type": " Customer Party ",
            "display_name": " Sender Name ",
        },
        beneficiary={
            "party_id": " beneficiary-001 ",
            "party_type": " Beneficiary Party ",
            "display_name": " Beneficiary Name ",
        },
    )

    assert value.sender == TransferPartyReference(
        party_id="sender-001",
        party_type="customer_party",
        display_name="Sender Name",
    )

    assert value.beneficiary == TransferPartyReference(
        party_id="beneficiary-001",
        party_type="beneficiary_party",
        display_name="Beneficiary Name",
    )


def test_factory_normalizes_account_references() -> None:
    value = transfer(
        source_account={
            "account_id": " wallet-aud ",
            "account_type": " Digital Wallet ",
            "currency_code": "aud",
            "institution_reference": " NovaPay AU ",
        },
        destination_account={
            "account_id": " wallet-usd ",
            "account_type": " Digital Wallet ",
            "currency_code": "usd",
            "institution_reference": " NovaPay US ",
        },
    )

    assert value.source_account == (
        TransferAccountReference(
            account_id="wallet-aud",
            account_type="digital_wallet",
            currency_code="AUD",
            institution_reference="NovaPay AU",
        )
    )

    assert value.destination_account == (
        TransferAccountReference(
            account_id="wallet-usd",
            account_type="digital_wallet",
            currency_code="USD",
            institution_reference="NovaPay US",
        )
    )


def test_factory_preserves_money_instances() -> None:
    source = money("100.00", "AUD")
    destination = money("65.00", "USD")

    value = transfer(
        source_amount=source,
        destination_amount=destination,
    )

    assert value.source_amount is source
    assert value.destination_amount is destination


def test_source_currency_code() -> None:
    assert transfer().source_currency_code == "AUD"


def test_destination_currency_code() -> None:
    assert transfer().destination_currency_code == "USD"


def test_cross_currency_transfer() -> None:
    assert transfer().is_cross_currency is True


def test_same_currency_transfer() -> None:
    value = transfer(
        destination_account={
            "account_id": "wallet-aud-destination",
            "account_type": "wallet",
            "currency_code": "AUD",
        },
        destination_amount=money("100.00", "AUD"),
        transfer_type="internal",
        direction="internal",
    )

    assert value.is_cross_currency is False


@pytest.mark.parametrize(
    "status",
    [
        TransferStatus.COMPLETED,
        TransferStatus.FAILED,
        TransferStatus.CANCELLED,
        TransferStatus.REVERSED,
        TransferStatus.EXPIRED,
    ],
)
def test_terminal_statuses(
    status: TransferStatus,
) -> None:
    assert transfer(status=status).is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        TransferStatus.DRAFT,
        TransferStatus.VALIDATED,
        TransferStatus.AUTHORIZED,
        TransferStatus.SUBMITTED,
        TransferStatus.PROCESSING,
    ],
)
def test_non_terminal_statuses(
    status: TransferStatus,
) -> None:
    assert transfer(status=status).is_terminal is False


def test_transfer_is_immutable() -> None:
    value = transfer()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_transfer_uses_slots() -> None:
    assert not hasattr(transfer(), "__dict__")


def test_transfer_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(Transfer)
    } == {
        "transfer_id",
        "reference",
        "status",
        "transfer_type",
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


def test_transfer_metadata_normalization() -> None:
    value = transfer(
        metadata={
            "Channel Name": "mobile",
            "tags": [
                "consumer",
                "international",
            ],
        }
    )

    assert value.metadata == TransferMetadata.of(
        {
            "channel_name": "mobile",
            "tags": (
                "consumer",
                "international",
            ),
        }
    )


def test_transfer_rejects_non_money_source_amount() -> None:
    with pytest.raises(
        TypeError,
        match="source amount must be Money",
    ):
        transfer(
            source_amount="100.00",  # type: ignore[arg-type]
        )


def test_transfer_rejects_non_money_destination_amount() -> None:
    with pytest.raises(
        TypeError,
        match="destination amount must be Money",
    ):
        transfer(
            destination_amount="65.00",  # type: ignore[arg-type]
        )


def test_transfer_rejects_source_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="source account currency",
    ):
        transfer(
            source_account={
                "account_id": "wallet-source",
                "account_type": "wallet",
                "currency_code": "USD",
            },
            source_amount=money("100.00", "AUD"),
        )


def test_transfer_rejects_destination_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="destination account currency",
    ):
        transfer(
            destination_account={
                "account_id": "wallet-destination",
                "account_type": "wallet",
                "currency_code": "AUD",
            },
            destination_amount=money("65.00", "USD"),
        )


def test_transfer_allows_account_without_currency() -> None:
    value = transfer(
        source_account={
            "account_id": "wallet-source",
            "account_type": "wallet",
        },
        destination_account={
            "account_id": "wallet-destination",
            "account_type": "wallet",
        },
    )

    assert value.source_account.currency_code is None
    assert value.destination_account.currency_code is None


def test_transfer_rejects_identical_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="same party and account",
    ):
        transfer(
            sender={
                "party_id": "party-001",
                "party_type": "customer",
            },
            beneficiary={
                "party_id": "party-001",
                "party_type": "customer",
            },
            source_account={
                "account_id": "wallet-001",
                "account_type": "wallet",
                "currency_code": "AUD",
            },
            destination_account={
                "account_id": "wallet-001",
                "account_type": "wallet",
                "currency_code": "USD",
            },
        )


def test_transfer_allows_same_party_different_accounts() -> None:
    value = transfer(
        sender={
            "party_id": "party-001",
            "party_type": "customer",
        },
        beneficiary={
            "party_id": "party-001",
            "party_type": "customer",
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
    )

    assert value.sender.party_id == (
        value.beneficiary.party_id
    )
    assert (
        value.source_account.account_id
        != value.destination_account.account_id
    )


def test_transfer_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        transfer(
            created_at=datetime(
                2026,
                8,
                3,
                5,
                0,
            )
        )


def test_transfer_normalizes_created_at_to_utc() -> None:
    local_timezone = timezone(timedelta(hours=10))

    value = transfer(
        created_at=datetime(
            2026,
            8,
            3,
            15,
            0,
            tzinfo=local_timezone,
        )
    )

    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_direct_construction_rejects_backdated_updated_at() -> None:
    base = transfer()

    with pytest.raises(
        ValueError,
        match="must not be earlier than created_at",
    ):
        Transfer(
            transfer_id=base.transfer_id,
            reference=base.reference,
            status=base.status,
            transfer_type=base.transfer_type,
            direction=base.direction,
            purpose=base.purpose,
            priority=base.priority,
            sender=base.sender,
            beneficiary=base.beneficiary,
            source_account=base.source_account,
            destination_account=base.destination_account,
            source_amount=base.source_amount,
            destination_amount=base.destination_amount,
            metadata=base.metadata,
            created_at=CREATED_AT,
            updated_at=CREATED_AT - timedelta(seconds=1),
            version=1,
        )


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_transfer_rejects_non_positive_version(
    version: int,
) -> None:
    base = transfer()

    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        Transfer(
            transfer_id=base.transfer_id,
            reference=base.reference,
            status=base.status,
            transfer_type=base.transfer_type,
            direction=base.direction,
            purpose=base.purpose,
            priority=base.priority,
            sender=base.sender,
            beneficiary=base.beneficiary,
            source_account=base.source_account,
            destination_account=base.destination_account,
            source_amount=base.source_amount,
            destination_amount=base.destination_amount,
            metadata=base.metadata,
            created_at=base.created_at,
            updated_at=base.updated_at,
            version=version,
        )


@pytest.mark.parametrize(
    "version",
    [
        True,
        1.5,
        "1",
    ],
)
def test_transfer_rejects_non_integer_version(
    version: object,
) -> None:
    base = transfer()

    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        Transfer(
            transfer_id=base.transfer_id,
            reference=base.reference,
            status=base.status,
            transfer_type=base.transfer_type,
            direction=base.direction,
            purpose=base.purpose,
            priority=base.priority,
            sender=base.sender,
            beneficiary=base.beneficiary,
            source_account=base.source_account,
            destination_account=base.destination_account,
            source_amount=base.source_amount,
            destination_amount=base.destination_amount,
            metadata=base.metadata,
            created_at=base.created_at,
            updated_at=base.updated_at,
            version=version,  # type: ignore[arg-type]
        )


def test_transfer_canonical_dict() -> None:
    payload = transfer().canonical_dict()

    assert list(payload) == [
        "transfer_id",
        "reference",
        "status",
        "transfer_type",
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

    assert payload["transfer_id"] == "transfer-001"
    assert payload["reference"] == "reference-001"
    assert payload["status"] == "draft"
    assert payload["transfer_type"] == "international"
    assert payload["direction"] == "outbound"
    assert payload["purpose"] == "family_support"
    assert payload["priority"] == "high"
    assert payload["sender"] == {
        "party_id": "sender-001",
        "party_type": "customer",
        "display_name": "Sender",
    }
    assert payload["beneficiary"] == {
        "party_id": "beneficiary-001",
        "party_type": "beneficiary",
        "display_name": "Beneficiary",
    }
    assert payload["source_account"] == {
        "account_id": "wallet-aud",
        "account_type": "wallet",
        "currency_code": "AUD",
        "institution_reference": "novapay-au",
    }
    assert payload["destination_account"] == {
        "account_id": "wallet-usd",
        "account_type": "wallet",
        "currency_code": "USD",
        "institution_reference": "novapay-us",
    }
    assert payload["metadata"] == {
        "channel": "mobile",
        "corridor": "AU-US",
    }
    assert payload["created_at"] == (
        "2026-08-03T05:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-03T05:00:00+00:00"
    )
    assert payload["version"] == 1


def test_canonical_dict_preserves_money_currency() -> None:
    payload = transfer().canonical_dict()

    source_payload = payload["source_amount"]
    destination_payload = payload["destination_amount"]

    assert isinstance(source_payload, dict)
    assert isinstance(destination_payload, dict)

    source_text = str(source_payload)
    destination_text = str(destination_payload)

    assert "AUD" in source_text
    assert "USD" in destination_text


def test_canonical_dict_is_fresh() -> None:
    value = transfer()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["sender"] is not second["sender"]
    assert first["beneficiary"] is not second["beneficiary"]
    assert first["source_account"] is not second["source_account"]
    assert first["destination_account"] is not second["destination_account"]
    assert first["source_amount"] is not second["source_amount"]
    assert first["destination_amount"] is not second["destination_amount"]
    assert first["metadata"] is not second["metadata"]


def test_transfer_contains_no_runtime_authority() -> None:
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


def test_transfer_fields_contain_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(Transfer)
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "settlement_engine",
        "provider_client",
        "http_client",
        "api_key",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names


def test_transfer_aggregate_is_exported_from_domain() -> None:
    import afritech.novapay.domain as domain

    assert domain.Transfer is Transfer
