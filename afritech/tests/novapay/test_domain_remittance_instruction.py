from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.remittance import (
    RemittanceCorridor,
    RemittanceFundingReference,
    RemittanceId,
    RemittanceInstruction,
    RemittanceInstructionId,
    RemittanceInstructionMetadata,
    RemittanceRecipientReference,
)
from afritech.novapay.domain.transfer import (
    TransferAccountReference,
    TransferPartyReference,
)


REQUESTED_AT = datetime(
    2026,
    8,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)

EXPIRES_AT = REQUESTED_AT + timedelta(minutes=30)


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


def funding_account(
    *,
    currency_code: str = "AUD",
) -> TransferAccountReference:
    return TransferAccountReference(
        account_id="wallet-aud",
        account_type="wallet",
        currency_code=currency_code,
    )


def recipient_party() -> TransferPartyReference:
    return TransferPartyReference(
        party_id="beneficiary-001",
        party_type="beneficiary",
    )


def recipient_account(
    *,
    currency_code: str = "BIF",
) -> TransferAccountReference:
    return TransferAccountReference(
        account_id="wallet-bif",
        account_type="wallet",
        currency_code=currency_code,
    )


def funding_reference(
    *,
    account_reference: TransferAccountReference | None = None,
    authorization_reference: object = "approval/001",
) -> RemittanceFundingReference:
    return RemittanceFundingReference.create(
        funding_source_id="funding-001",
        funding_source_type="mobile wallet",
        account_reference=(
            account_reference
            if account_reference is not None
            else funding_account()
        ),
        authorization_reference=authorization_reference,
    )


def recipient_reference(
    *,
    account_reference: TransferAccountReference | None = None,
    routing_reference: object = "route/BI/001",
) -> RemittanceRecipientReference:
    return RemittanceRecipientReference.create(
        recipient_id="recipient-001",
        recipient_type="beneficiary",
        party_reference=recipient_party(),
        account_reference=(
            account_reference
            if account_reference is not None
            else recipient_account()
        ),
        delivery_method="mobile wallet",
        routing_reference=routing_reference,
    )


def corridor(
    *,
    source_country_code: object = "AU",
    destination_country_code: object = "BI",
    source_currency_code: object = "AUD",
    destination_currency_code: object = "BIF",
) -> RemittanceCorridor:
    return RemittanceCorridor.create(
        source_country_code=source_country_code,
        destination_country_code=destination_country_code,
        source_currency_code=source_currency_code,
        destination_currency_code=destination_currency_code,
    )


def instruction(
    *,
    instruction_id: object = "instruction-001",
    remittance_id: object = "remittance-001",
    funding_value: RemittanceFundingReference | None = None,
    recipient_value: RemittanceRecipientReference | None = None,
    corridor_value: RemittanceCorridor | None = None,
    requested_source_amount: Money | None = None,
    expected_destination_amount: Money | None = None,
    requested_at: datetime = REQUESTED_AT,
    expires_at: datetime | None = EXPIRES_AT,
    metadata: object = None,
    version: int = 1,
) -> RemittanceInstruction:
    return RemittanceInstruction.create(
        instruction_id=instruction_id,
        remittance_id=remittance_id,
        funding_reference=(
            funding_value
            if funding_value is not None
            else funding_reference()
        ),
        recipient_reference=(
            recipient_value
            if recipient_value is not None
            else recipient_reference()
        ),
        corridor=(
            corridor_value
            if corridor_value is not None
            else corridor()
        ),
        requested_source_amount=(
            requested_source_amount
            if requested_source_amount is not None
            else money("100.00", "AUD")
        ),
        expected_destination_amount=(
            expected_destination_amount
            if expected_destination_amount is not None
            else money("185000.00", "BIF")
        ),
        requested_at=requested_at,
        expires_at=expires_at,
        metadata=(
            metadata
            if metadata is not None
            else {
                "channel": "mobile",
                "quote_reference": "quote-001",
            }
        ),
        version=version,
    )


@pytest.mark.parametrize(
    "value",
    [
        "instruction-001",
        "instruction:au-bi:001",
        "instruction_001",
        "INS.2026.001",
        "i1",
        "x" * 128,
    ],
)
def test_instruction_id_accepts_valid_values(
    value: str,
) -> None:
    result = RemittanceInstructionId.of(value)

    assert result.value == value
    assert str(result) == value


def test_instruction_id_preserves_instance() -> None:
    value = RemittanceInstructionId.of(
        "instruction-001"
    )

    assert RemittanceInstructionId.of(value) is value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "-invalid",
        ".invalid",
        ":invalid",
        "_invalid",
        "invalid value",
        "invalid/value",
        "x" * 129,
    ],
)
def test_instruction_id_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        RemittanceInstructionId.of(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        object(),
    ],
)
def test_instruction_id_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        RemittanceInstructionId.of(value)


def test_instruction_id_is_orderable() -> None:
    values = sorted(
        [
            RemittanceInstructionId.of("instruction-002"),
            RemittanceInstructionId.of("instruction-001"),
        ]
    )

    assert [
        value.value
        for value in values
    ] == [
        "instruction-001",
        "instruction-002",
    ]


def test_instruction_id_is_immutable() -> None:
    value = RemittanceInstructionId.of(
        "instruction-001"
    )

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


def test_funding_reference_construction() -> None:
    account = funding_account()
    value = RemittanceFundingReference.create(
        funding_source_id="funding-001",
        funding_source_type="mobile wallet",
        account_reference=account,
        authorization_reference="approval/001",
    )

    assert value.funding_source_id == "funding-001"
    assert value.funding_source_type == "mobile_wallet"
    assert value.account_reference is account
    assert value.authorization_reference == "approval/001"
    assert value.currency_code == "AUD"


def test_funding_reference_without_authorization() -> None:
    value = funding_reference(
        authorization_reference=None,
    )

    assert value.authorization_reference is None


def test_funding_reference_is_immutable() -> None:
    value = funding_reference()

    with pytest.raises(FrozenInstanceError):
        value.funding_source_id = "changed"  # type: ignore[misc]


def test_funding_reference_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceFundingReference)
    } == {
        "funding_source_id",
        "funding_source_type",
        "account_reference",
        "authorization_reference",
    }


def test_funding_reference_canonical_dict() -> None:
    payload = funding_reference().canonical_dict()

    assert list(payload) == [
        "funding_source_id",
        "funding_source_type",
        "account_reference",
        "authorization_reference",
    ]
    assert payload["funding_source_id"] == "funding-001"
    assert payload["funding_source_type"] == "mobile_wallet"
    assert payload["account_reference"]["account_id"] == (
        "wallet-aud"
    )
    assert payload["account_reference"]["currency_code"] == (
        "AUD"
    )
    assert payload["authorization_reference"] == (
        "approval/001"
    )


def test_funding_reference_canonical_dict_is_fresh() -> None:
    value = funding_reference()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["account_reference"]
        is not second["account_reference"]
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("funding_source_id", ""),
        ("funding_source_type", ""),
    ],
)
def test_funding_reference_rejects_empty_values(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "funding_source_id": "funding-001",
        "funding_source_type": "wallet",
        "account_reference": funding_account(),
        field_name: value,
    }

    with pytest.raises(ValueError):
        RemittanceFundingReference.create(**kwargs)


def test_funding_reference_rejects_wrong_account_type() -> None:
    with pytest.raises(
        TypeError,
        match="TransferAccountReference",
    ):
        RemittanceFundingReference.create(
            funding_source_id="funding-001",
            funding_source_type="wallet",
            account_reference=object(),  # type: ignore[arg-type]
        )


def test_funding_reference_rejects_invalid_authorization() -> None:
    with pytest.raises(ValueError):
        funding_reference(
            authorization_reference="/invalid",
        )


def test_recipient_reference_construction() -> None:
    party = recipient_party()
    account = recipient_account()

    value = RemittanceRecipientReference.create(
        recipient_id="recipient-001",
        recipient_type="beneficiary",
        party_reference=party,
        account_reference=account,
        delivery_method="mobile wallet",
        routing_reference="route/BI/001",
    )

    assert value.recipient_id == "recipient-001"
    assert value.recipient_type == "beneficiary"
    assert value.party_reference is party
    assert value.account_reference is account
    assert value.delivery_method == "mobile_wallet"
    assert value.routing_reference == "route/BI/001"
    assert value.currency_code == "BIF"


def test_recipient_reference_without_routing() -> None:
    value = recipient_reference(
        routing_reference=None,
    )

    assert value.routing_reference is None


def test_recipient_reference_is_immutable() -> None:
    value = recipient_reference()

    with pytest.raises(FrozenInstanceError):
        value.recipient_id = "changed"  # type: ignore[misc]


def test_recipient_reference_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceRecipientReference)
    } == {
        "recipient_id",
        "recipient_type",
        "party_reference",
        "account_reference",
        "delivery_method",
        "routing_reference",
    }


def test_recipient_reference_canonical_dict() -> None:
    payload = recipient_reference().canonical_dict()

    assert list(payload) == [
        "recipient_id",
        "recipient_type",
        "party_reference",
        "account_reference",
        "delivery_method",
        "routing_reference",
    ]
    assert payload["recipient_id"] == "recipient-001"
    assert payload["recipient_type"] == "beneficiary"
    assert payload["party_reference"]["party_id"] == (
        "beneficiary-001"
    )
    assert payload["account_reference"]["account_id"] == (
        "wallet-bif"
    )
    assert payload["delivery_method"] == "mobile_wallet"
    assert payload["routing_reference"] == "route/BI/001"


def test_recipient_reference_canonical_dict_is_fresh() -> None:
    value = recipient_reference()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["party_reference"]
        is not second["party_reference"]
    )
    assert (
        first["account_reference"]
        is not second["account_reference"]
    )


def test_recipient_reference_rejects_wrong_party_type() -> None:
    with pytest.raises(
        TypeError,
        match="TransferPartyReference",
    ):
        RemittanceRecipientReference.create(
            recipient_id="recipient-001",
            recipient_type="beneficiary",
            party_reference=object(),  # type: ignore[arg-type]
            account_reference=recipient_account(),
            delivery_method="mobile_wallet",
        )


def test_recipient_reference_rejects_wrong_account_type() -> None:
    with pytest.raises(
        TypeError,
        match="TransferAccountReference",
    ):
        RemittanceRecipientReference.create(
            recipient_id="recipient-001",
            recipient_type="beneficiary",
            party_reference=recipient_party(),
            account_reference=object(),  # type: ignore[arg-type]
            delivery_method="mobile_wallet",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("recipient_id", ""),
        ("recipient_type", ""),
        ("delivery_method", ""),
    ],
)
def test_recipient_reference_rejects_empty_values(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "recipient_id": "recipient-001",
        "recipient_type": "beneficiary",
        "party_reference": recipient_party(),
        "account_reference": recipient_account(),
        "delivery_method": "mobile_wallet",
        field_name: value,
    }

    with pytest.raises(ValueError):
        RemittanceRecipientReference.create(**kwargs)


def test_recipient_reference_rejects_invalid_routing() -> None:
    with pytest.raises(ValueError):
        recipient_reference(
            routing_reference="/invalid",
        )


@pytest.mark.parametrize(
    (
        "source_country",
        "destination_country",
        "source_currency",
        "destination_currency",
        "expected_code",
    ),
    [
        ("au", "bi", "aud", "bif", "AU-BI"),
        ("AU", "CD", "AUD", "CDF", "AU-CD"),
        ("BI", "BI", "BIF", "BIF", "BI-BI"),
    ],
)
def test_corridor_normalization(
    source_country: str,
    destination_country: str,
    source_currency: str,
    destination_currency: str,
    expected_code: str,
) -> None:
    value = corridor(
        source_country_code=source_country,
        destination_country_code=destination_country,
        source_currency_code=source_currency,
        destination_currency_code=destination_currency,
    )

    assert value.source_country_code == source_country.upper()
    assert (
        value.destination_country_code
        == destination_country.upper()
    )
    assert value.source_currency_code == source_currency.upper()
    assert (
        value.destination_currency_code
        == destination_currency.upper()
    )
    assert value.code == expected_code


def test_cross_border_corridor_classification() -> None:
    assert corridor().is_cross_border is True


def test_domestic_corridor_classification() -> None:
    value = corridor(
        source_country_code="BI",
        destination_country_code="BI",
        source_currency_code="BIF",
        destination_currency_code="BIF",
    )

    assert value.is_cross_border is False
    assert value.is_cross_currency is False


def test_cross_currency_corridor_classification() -> None:
    assert corridor().is_cross_currency is True


def test_same_currency_corridor_classification() -> None:
    value = corridor(
        source_country_code="AU",
        destination_country_code="NZ",
        source_currency_code="AUD",
        destination_currency_code="AUD",
    )

    assert value.is_cross_border is True
    assert value.is_cross_currency is False


def test_corridor_is_immutable() -> None:
    value = corridor()

    with pytest.raises(FrozenInstanceError):
        value.source_country_code = "US"  # type: ignore[misc]


def test_corridor_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceCorridor)
    } == {
        "source_country_code",
        "destination_country_code",
        "source_currency_code",
        "destination_currency_code",
    }


def test_corridor_canonical_dict() -> None:
    payload = corridor().canonical_dict()

    assert payload == {
        "source_country_code": "AU",
        "destination_country_code": "BI",
        "source_currency_code": "AUD",
        "destination_currency_code": "BIF",
    }


@pytest.mark.parametrize(
    "value",
    [
        "",
        "A",
        "AUS",
        "1A",
        "A1",
    ],
)
def test_corridor_rejects_invalid_country_codes(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        corridor(source_country_code=value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "AU",
        "AUDD",
        "1UD",
        "AU1",
    ],
)
def test_corridor_rejects_invalid_currency_codes(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        corridor(source_currency_code=value)


def test_instruction_metadata_defaults_empty() -> None:
    value = RemittanceInstructionMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_instruction_metadata_preserves_instance() -> None:
    value = RemittanceInstructionMetadata.of(
        {"channel": "mobile"}
    )

    assert RemittanceInstructionMetadata.of(value) is value


def test_instruction_metadata_normalizes_values() -> None:
    value = RemittanceInstructionMetadata.of(
        {
            "Channel": "mobile",
            "Quote Reference": "quote-001",
            "tags": ["consumer", "international"],
        }
    )

    assert value.values == {
        "channel": "mobile",
        "quote_reference": "quote-001",
        "tags": (
            "consumer",
            "international",
        ),
    }


def test_instruction_metadata_is_immutable() -> None:
    value = RemittanceInstructionMetadata.of(
        {"channel": "mobile"}
    )

    with pytest.raises(FrozenInstanceError):
        value.values = {}  # type: ignore[misc]

    with pytest.raises(TypeError):
        value.values["channel"] = "web"  # type: ignore[index]


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "access_token",
        "api_key",
        "password",
        "pin",
        "private_key",
        "secret",
        "token",
    ],
)
def test_instruction_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        RemittanceInstructionMetadata.of(
            {key: "sensitive"}
        )


def test_instruction_construction() -> None:
    value = instruction()

    assert value.instruction_id == (
        RemittanceInstructionId.of(
            "instruction-001"
        )
    )
    assert value.remittance_id == RemittanceId.of(
        "remittance-001"
    )
    assert value.source_currency_code == "AUD"
    assert value.destination_currency_code == "BIF"
    assert value.is_cross_border is True
    assert value.is_cross_currency is True
    assert value.requested_at == REQUESTED_AT
    assert value.expires_at == EXPIRES_AT
    assert value.version == 1


def test_instruction_preserves_domain_instances() -> None:
    instruction_id = RemittanceInstructionId.of(
        "instruction-001"
    )
    remittance_id = RemittanceId.of(
        "remittance-001"
    )
    funding = funding_reference()
    recipient = recipient_reference()
    corridor_value = corridor()
    source_amount = money("100.00", "AUD")
    destination_amount = money("185000.00", "BIF")
    metadata = RemittanceInstructionMetadata.of(
        {"channel": "mobile"}
    )

    value = instruction(
        instruction_id=instruction_id,
        remittance_id=remittance_id,
        funding_value=funding,
        recipient_value=recipient,
        corridor_value=corridor_value,
        requested_source_amount=source_amount,
        expected_destination_amount=destination_amount,
        metadata=metadata,
    )

    assert value.instruction_id is instruction_id
    assert value.remittance_id is remittance_id
    assert value.funding_reference is funding
    assert value.recipient_reference is recipient
    assert value.corridor is corridor_value
    assert value.requested_source_amount is source_amount
    assert value.expected_destination_amount is destination_amount
    assert value.metadata is metadata


def test_instruction_without_expiry() -> None:
    value = instruction(expires_at=None)

    assert value.expires_at is None
    assert value.is_expired(
        at=REQUESTED_AT + timedelta(days=30)
    ) is False


def test_instruction_expiry_classification() -> None:
    value = instruction()

    assert value.is_expired(
        at=REQUESTED_AT
    ) is False
    assert value.is_expired(
        at=EXPIRES_AT - timedelta(microseconds=1)
    ) is False
    assert value.is_expired(
        at=EXPIRES_AT
    ) is True
    assert value.is_expired(
        at=EXPIRES_AT + timedelta(seconds=1)
    ) is True


def test_instruction_datetime_normalizes_to_utc() -> None:
    offset = timezone(timedelta(hours=10))

    value = instruction(
        requested_at=datetime(
            2026,
            8,
            4,
            10,
            0,
            tzinfo=offset,
        ),
        expires_at=datetime(
            2026,
            8,
            4,
            10,
            30,
            tzinfo=offset,
        ),
    )

    assert value.requested_at == REQUESTED_AT
    assert value.expires_at == EXPIRES_AT
    assert value.requested_at.tzinfo is timezone.utc
    assert value.expires_at.tzinfo is timezone.utc


def test_instruction_is_immutable() -> None:
    value = instruction()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_instruction_field_contract() -> None:
    assert {
        item.name
        for item in fields(RemittanceInstruction)
    } == {
        "instruction_id",
        "remittance_id",
        "funding_reference",
        "recipient_reference",
        "corridor",
        "requested_source_amount",
        "expected_destination_amount",
        "requested_at",
        "expires_at",
        "metadata",
        "version",
    }


def test_instruction_canonical_dict() -> None:
    payload = instruction().canonical_dict()

    assert list(payload) == [
        "instruction_id",
        "remittance_id",
        "funding_reference",
        "recipient_reference",
        "corridor",
        "requested_source_amount",
        "expected_destination_amount",
        "requested_at",
        "expires_at",
        "metadata",
        "version",
    ]
    assert payload["instruction_id"] == "instruction-001"
    assert payload["remittance_id"] == "remittance-001"
    assert payload["funding_reference"][
        "funding_source_id"
    ] == "funding-001"
    assert payload["recipient_reference"][
        "recipient_id"
    ] == "recipient-001"
    assert payload["corridor"] == {
        "source_country_code": "AU",
        "destination_country_code": "BI",
        "source_currency_code": "AUD",
        "destination_currency_code": "BIF",
    }
    assert "AUD" in str(payload["requested_source_amount"])
    assert "BIF" in str(payload["expected_destination_amount"])
    assert payload["requested_at"] == (
        "2026-08-04T00:00:00+00:00"
    )
    assert payload["expires_at"] == (
        "2026-08-04T00:30:00+00:00"
    )
    assert payload["metadata"] == {
        "channel": "mobile",
        "quote_reference": "quote-001",
    }
    assert payload["version"] == 1


def test_instruction_canonical_dict_returns_fresh_payloads() -> None:
    value = instruction()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["funding_reference"]
        is not second["funding_reference"]
    )
    assert (
        first["recipient_reference"]
        is not second["recipient_reference"]
    )
    assert first["corridor"] is not second["corridor"]
    assert (
        first["requested_source_amount"]
        is not second["requested_source_amount"]
    )
    assert (
        first["expected_destination_amount"]
        is not second["expected_destination_amount"]
    )
    assert first["metadata"] is not second["metadata"]


def test_instruction_rejects_wrong_funding_type() -> None:
    with pytest.raises(
        TypeError,
        match="RemittanceFundingReference",
    ):
        instruction(
            funding_value=object(),  # type: ignore[arg-type]
        )


def test_instruction_rejects_wrong_recipient_type() -> None:
    with pytest.raises(
        TypeError,
        match="RemittanceRecipientReference",
    ):
        instruction(
            recipient_value=object(),  # type: ignore[arg-type]
        )


def test_instruction_rejects_wrong_corridor_type() -> None:
    with pytest.raises(
        TypeError,
        match="RemittanceCorridor",
    ):
        instruction(
            corridor_value=object(),  # type: ignore[arg-type]
        )


def test_instruction_rejects_source_corridor_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="source amount currency",
    ):
        instruction(
            requested_source_amount=money(
                "100.00",
                "USD",
            )
        )


def test_instruction_rejects_destination_corridor_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="destination amount currency",
    ):
        instruction(
            expected_destination_amount=money(
                "185000.00",
                "USD",
            )
        )


def test_instruction_rejects_funding_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="funding currency",
    ):
        instruction(
            funding_value=funding_reference(
                account_reference=funding_account(
                    currency_code="USD",
                )
            )
        )


def test_instruction_rejects_recipient_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="recipient currency",
    ):
        instruction(
            recipient_value=recipient_reference(
                account_reference=recipient_account(
                    currency_code="USD",
                )
            )
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "requested_at",
        "expires_at",
    ],
)
def test_instruction_rejects_naive_datetimes(
    field_name: str,
) -> None:
    kwargs = {
        field_name: datetime(
            2026,
            8,
            4,
            0,
            0,
        )
    }

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        instruction(**kwargs)


@pytest.mark.parametrize(
    "expires_at",
    [
        REQUESTED_AT,
        REQUESTED_AT - timedelta(seconds=1),
    ],
)
def test_instruction_expiry_must_be_future(
    expires_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="later than requested_at",
    ):
        instruction(expires_at=expires_at)


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_instruction_rejects_non_positive_version(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        instruction(version=version)


@pytest.mark.parametrize(
    "version",
    [
        True,
        False,
        1.5,
        "1",
        None,
    ],
)
def test_instruction_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        instruction(
            version=version,  # type: ignore[arg-type]
        )


def test_instruction_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        instruction(
            metadata={
                "authorization": "secret",
            }
        )


def test_instruction_expiry_check_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        instruction().is_expired(
            at=datetime(
                2026,
                8,
                4,
                0,
                0,
            )
        )


def test_instruction_domain_is_publicly_exported() -> None:
    import afritech.novapay as novapay
    import afritech.novapay.domain as domain
    import afritech.novapay.domain.remittance as remittance

    for symbol in (
        "RemittanceInstructionId",
        "RemittanceFundingReference",
        "RemittanceRecipientReference",
        "RemittanceCorridor",
        "RemittanceInstructionMetadata",
        "RemittanceInstruction",
    ):
        module_value = getattr(remittance, symbol)

        assert getattr(domain, symbol) is module_value
        assert getattr(novapay, symbol) is module_value
        assert symbol in domain.__all__
        assert symbol in novapay.__all__


def test_instruction_domain_has_no_runtime_authority() -> None:
    value_types = (
        RemittanceFundingReference,
        RemittanceRecipientReference,
        RemittanceCorridor,
        RemittanceInstruction,
    )

    for value_type in value_types:
        names = {
            name
            for name in dir(value_type)
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
            "submit",
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


def test_instruction_fields_have_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(RemittanceInstruction)
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
