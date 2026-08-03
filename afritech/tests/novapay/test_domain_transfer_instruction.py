from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest

from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.transfer import (
    TransferBeneficiaryReference,
    TransferFundingReference,
    TransferInstruction,
    TransferInstructionId,
    TransferInstructionMetadata,
)


REQUESTED_AT = datetime(
    2026,
    8,
    3,
    5,
    15,
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


def funding_reference(
    *,
    currency_code: str | None = "AUD",
) -> TransferFundingReference:
    return TransferFundingReference.of(
        {
            "funding_source_id": "funding-wallet-aud",
            "funding_source_type": "wallet",
            "account_reference": {
                "account_id": "wallet-aud",
                "account_type": "wallet",
                "currency_code": currency_code,
                "institution_reference": "novapay-au",
            },
            "authorization_reference": "auth-001",
        }
    )


def beneficiary_reference(
    *,
    currency_code: str | None = "USD",
) -> TransferBeneficiaryReference:
    return TransferBeneficiaryReference.of(
        {
            "beneficiary_id": "beneficiary-001",
            "beneficiary_type": "registered",
            "party_reference": {
                "party_id": "customer-beneficiary",
                "party_type": "beneficiary",
                "display_name": "Beneficiary Customer",
            },
            "account_reference": {
                "account_id": "wallet-usd",
                "account_type": "wallet",
                "currency_code": currency_code,
                "institution_reference": "novapay-us",
            },
            "delivery_method": "wallet_credit",
            "routing_reference": "route-us-001",
        }
    )


def instruction(
    *,
    instruction_id: object = "instruction-001",
    transfer_id: object = "transfer-001",
    funding: object | None = None,
    beneficiary: object | None = None,
    source_amount: Money | None = None,
    destination_amount: Money | None = None,
    requested_at: datetime = REQUESTED_AT,
    expires_at: datetime | None = EXPIRES_AT,
    metadata: object = None,
) -> TransferInstruction:
    return TransferInstruction.create(
        instruction_id=instruction_id,
        transfer_id=transfer_id,
        funding_reference=(
            funding
            if funding is not None
            else funding_reference()
        ),
        beneficiary_reference=(
            beneficiary
            if beneficiary is not None
            else beneficiary_reference()
        ),
        requested_source_amount=(
            source_amount
            if source_amount is not None
            else money("100.00", "AUD")
        ),
        expected_destination_amount=(
            destination_amount
            if destination_amount is not None
            else money("65.00", "USD")
        ),
        requested_at=requested_at,
        expires_at=expires_at,
        metadata=(
            metadata
            if metadata is not None
            else {
                "channel": "mobile",
                "corridor": "AU-US",
            }
        ),
    )


def test_instruction_id_normalizes() -> None:
    value = TransferInstructionId(
        " instruction-001 "
    )

    assert value.value == "instruction-001"
    assert value.canonical() == "instruction-001"
    assert str(value) == "instruction-001"


def test_instruction_id_of_preserves_instance() -> None:
    value = TransferInstructionId(
        "instruction-001"
    )

    assert TransferInstructionId.of(value) is value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        None,
        1,
    ],
)
def test_instruction_id_rejects_invalid_value(
    value: object,
) -> None:
    expected = (
        TypeError
        if not isinstance(value, str)
        else ValueError
    )

    with pytest.raises(expected):
        TransferInstructionId.of(value)


def test_instruction_id_is_immutable() -> None:
    value = TransferInstructionId(
        "instruction-001"
    )

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


def test_funding_reference_normalizes() -> None:
    value = TransferFundingReference(
        funding_source_id=" funding-001 ",
        funding_source_type=" Digital Wallet ",
        account_reference={
            "account_id": " wallet-aud ",
            "account_type": " Wallet ",
            "currency_code": "aud",
            "institution_reference": " NovaPay AU ",
        },
        authorization_reference=" auth-001 ",
    )

    assert value.funding_source_id == "funding-001"
    assert value.funding_source_type == (
        "digital_wallet"
    )
    assert value.account_reference.account_id == (
        "wallet-aud"
    )
    assert value.account_reference.currency_code == (
        "AUD"
    )
    assert value.authorization_reference == "auth-001"


def test_funding_reference_preserves_instance() -> None:
    value = funding_reference()

    assert TransferFundingReference.of(value) is value


def test_funding_reference_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        TransferFundingReference.of("funding-001")


def test_funding_reference_canonical_dict() -> None:
    payload = funding_reference().canonical_dict()

    assert payload == {
        "funding_source_id": "funding-wallet-aud",
        "funding_source_type": "wallet",
        "account_reference": {
            "account_id": "wallet-aud",
            "account_type": "wallet",
            "currency_code": "AUD",
            "institution_reference": "novapay-au",
        },
        "authorization_reference": "auth-001",
    }


def test_funding_reference_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(
            TransferFundingReference
        )
    } == {
        "funding_source_id",
        "funding_source_type",
        "account_reference",
        "authorization_reference",
    }


def test_beneficiary_reference_normalizes() -> None:
    value = TransferBeneficiaryReference(
        beneficiary_id=" beneficiary-001 ",
        beneficiary_type=" Registered Beneficiary ",
        party_reference={
            "party_id": " customer-001 ",
            "party_type": " Beneficiary Party ",
            "display_name": " Customer Name ",
        },
        account_reference={
            "account_id": " wallet-usd ",
            "account_type": " Wallet ",
            "currency_code": "usd",
            "institution_reference": " NovaPay US ",
        },
        delivery_method=" Wallet Credit ",
        routing_reference=" route-001 ",
    )

    assert value.beneficiary_id == "beneficiary-001"
    assert value.beneficiary_type == (
        "registered_beneficiary"
    )
    assert value.party_reference.party_id == (
        "customer-001"
    )
    assert value.account_reference.currency_code == (
        "USD"
    )
    assert value.delivery_method == "wallet_credit"
    assert value.routing_reference == "route-001"


def test_beneficiary_reference_preserves_instance() -> None:
    value = beneficiary_reference()

    assert TransferBeneficiaryReference.of(
        value
    ) is value


def test_beneficiary_reference_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        TransferBeneficiaryReference.of(
            "beneficiary-001"
        )


def test_beneficiary_reference_canonical_dict() -> None:
    payload = beneficiary_reference().canonical_dict()

    assert payload["beneficiary_id"] == (
        "beneficiary-001"
    )
    assert payload["beneficiary_type"] == "registered"
    assert payload["party_reference"][
        "party_id"
    ] == "customer-beneficiary"
    assert payload["account_reference"][
        "currency_code"
    ] == "USD"
    assert payload["delivery_method"] == (
        "wallet_credit"
    )
    assert payload["routing_reference"] == (
        "route-us-001"
    )


def test_beneficiary_reference_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(
            TransferBeneficiaryReference
        )
    } == {
        "beneficiary_id",
        "beneficiary_type",
        "party_reference",
        "account_reference",
        "delivery_method",
        "routing_reference",
    }


def test_instruction_metadata_defaults_empty() -> None:
    value = TransferInstructionMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_instruction_metadata_normalizes() -> None:
    value = TransferInstructionMetadata.of(
        {
            "Channel Name": "mobile",
            "tags": [
                "consumer",
                "priority",
            ],
        }
    )

    assert value.values["channel_name"] == "mobile"
    assert value.values["tags"] == (
        "consumer",
        "priority",
    )


def test_instruction_metadata_preserves_instance() -> None:
    value = TransferInstructionMetadata.of(
        {
            "channel": "mobile",
        }
    )

    assert TransferInstructionMetadata.of(
        value
    ) is value


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "password",
        "access_token",
        "credentials",
        "private-key",
        "pin",
    ],
)
def test_instruction_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        TransferInstructionMetadata.of(
            {
                key: "sensitive",
            }
        )


def test_create_transfer_instruction() -> None:
    value = instruction()

    assert value.instruction_id == (
        TransferInstructionId(
            "instruction-001"
        )
    )
    assert value.transfer_id.value == "transfer-001"
    assert value.version == 1
    assert value.requested_at == REQUESTED_AT
    assert value.expires_at == EXPIRES_AT


def test_instruction_factory_normalizes_ids() -> None:
    value = instruction(
        instruction_id=" instruction-001 ",
        transfer_id=" transfer-001 ",
    )

    assert value.instruction_id.value == (
        "instruction-001"
    )
    assert value.transfer_id.value == "transfer-001"


def test_instruction_preserves_reference_instances() -> None:
    funding = funding_reference()
    beneficiary = beneficiary_reference()

    value = instruction(
        funding=funding,
        beneficiary=beneficiary,
    )

    assert value.funding_reference is funding
    assert value.beneficiary_reference is beneficiary


def test_instruction_preserves_money_instances() -> None:
    source = money("100.00", "AUD")
    destination = money("65.00", "USD")

    value = instruction(
        source_amount=source,
        destination_amount=destination,
    )

    assert value.requested_source_amount is source
    assert value.expected_destination_amount is destination


def test_instruction_currency_codes() -> None:
    value = instruction()

    assert value.source_currency_code == "AUD"
    assert value.destination_currency_code == "USD"
    assert value.is_cross_currency is True


def test_same_currency_instruction() -> None:
    value = instruction(
        beneficiary=beneficiary_reference(
            currency_code="AUD"
        ),
        destination_amount=money(
            "100.00",
            "AUD",
        ),
    )

    assert value.is_cross_currency is False


def test_instruction_without_expiry() -> None:
    value = instruction(expires_at=None)

    assert value.expires_at is None
    assert value.is_expired(
        at=REQUESTED_AT + timedelta(days=365)
    ) is False


def test_instruction_expiry_boundary() -> None:
    value = instruction()

    assert value.is_expired(
        at=EXPIRES_AT - timedelta(microseconds=1)
    ) is False

    assert value.is_expired(
        at=EXPIRES_AT
    ) is True

    assert value.is_expired(
        at=EXPIRES_AT + timedelta(seconds=1)
    ) is True


def test_instruction_expiry_check_normalizes_timezone() -> None:
    value = instruction()
    local_timezone = timezone(
        timedelta(hours=10)
    )

    local_expiry = datetime(
        2026,
        8,
        3,
        15,
        45,
        tzinfo=local_timezone,
    )

    assert value.is_expired(
        at=local_expiry
    ) is True


def test_instruction_rejects_naive_expiry_check() -> None:
    value = instruction()

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        value.is_expired(
            at=datetime(
                2026,
                8,
                3,
                5,
                45,
            )
        )


def test_instruction_rejects_non_money_source() -> None:
    with pytest.raises(
        TypeError,
        match="source amount must be Money",
    ):
        instruction(
            source_amount="100.00",  # type: ignore[arg-type]
        )


def test_instruction_rejects_non_money_destination() -> None:
    with pytest.raises(
        TypeError,
        match="destination amount must be Money",
    ):
        instruction(
            destination_amount="65.00",  # type: ignore[arg-type]
        )


def test_instruction_rejects_funding_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="funding account currency",
    ):
        instruction(
            funding=funding_reference(
                currency_code="USD"
            ),
            source_amount=money(
                "100.00",
                "AUD",
            ),
        )


def test_instruction_rejects_beneficiary_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="beneficiary account currency",
    ):
        instruction(
            beneficiary=beneficiary_reference(
                currency_code="AUD"
            ),
            destination_amount=money(
                "65.00",
                "USD",
            ),
        )


def test_instruction_allows_missing_account_currencies() -> None:
    value = instruction(
        funding=funding_reference(
            currency_code=None
        ),
        beneficiary=beneficiary_reference(
            currency_code=None
        ),
    )

    assert (
        value.funding_reference
        .account_reference
        .currency_code
        is None
    )
    assert (
        value.beneficiary_reference
        .account_reference
        .currency_code
        is None
    )


@pytest.mark.parametrize(
    "expires_at",
    [
        REQUESTED_AT,
        REQUESTED_AT - timedelta(seconds=1),
    ],
)
def test_instruction_rejects_invalid_expiry(
    expires_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="later than requested_at",
    ):
        instruction(expires_at=expires_at)


def test_instruction_rejects_naive_requested_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        instruction(
            requested_at=datetime(
                2026,
                8,
                3,
                5,
                15,
            )
        )


def test_instruction_rejects_naive_expires_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        instruction(
            expires_at=datetime(
                2026,
                8,
                3,
                5,
                45,
            )
        )


def test_instruction_normalizes_timestamps_to_utc() -> None:
    local_timezone = timezone(
        timedelta(hours=10)
    )

    value = instruction(
        requested_at=datetime(
            2026,
            8,
            3,
            15,
            15,
            tzinfo=local_timezone,
        ),
        expires_at=datetime(
            2026,
            8,
            3,
            15,
            45,
            tzinfo=local_timezone,
        ),
    )

    assert value.requested_at == REQUESTED_AT
    assert value.expires_at == EXPIRES_AT


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
    value = instruction()

    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        TransferInstruction(
            instruction_id=value.instruction_id,
            transfer_id=value.transfer_id,
            funding_reference=value.funding_reference,
            beneficiary_reference=(
                value.beneficiary_reference
            ),
            requested_source_amount=(
                value.requested_source_amount
            ),
            expected_destination_amount=(
                value.expected_destination_amount
            ),
            requested_at=value.requested_at,
            expires_at=value.expires_at,
            metadata=value.metadata,
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
def test_instruction_rejects_non_integer_version(
    version: object,
) -> None:
    value = instruction()

    with pytest.raises(
        TypeError,
        match="version must be an integer",
    ):
        TransferInstruction(
            instruction_id=value.instruction_id,
            transfer_id=value.transfer_id,
            funding_reference=value.funding_reference,
            beneficiary_reference=(
                value.beneficiary_reference
            ),
            requested_source_amount=(
                value.requested_source_amount
            ),
            expected_destination_amount=(
                value.expected_destination_amount
            ),
            requested_at=value.requested_at,
            expires_at=value.expires_at,
            metadata=value.metadata,
            version=version,  # type: ignore[arg-type]
        )


def test_instruction_is_immutable() -> None:
    value = instruction()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_instruction_uses_slots() -> None:
    assert not hasattr(instruction(), "__dict__")


def test_instruction_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(TransferInstruction)
    } == {
        "instruction_id",
        "transfer_id",
        "funding_reference",
        "beneficiary_reference",
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
        "transfer_id",
        "funding_reference",
        "beneficiary_reference",
        "requested_source_amount",
        "expected_destination_amount",
        "requested_at",
        "expires_at",
        "metadata",
        "version",
    ]

    assert payload["instruction_id"] == (
        "instruction-001"
    )
    assert payload["transfer_id"] == "transfer-001"
    assert payload["funding_reference"][
        "funding_source_id"
    ] == "funding-wallet-aud"
    assert payload["beneficiary_reference"][
        "beneficiary_id"
    ] == "beneficiary-001"
    assert payload["requested_at"] == (
        "2026-08-03T05:15:00+00:00"
    )
    assert payload["expires_at"] == (
        "2026-08-03T05:45:00+00:00"
    )
    assert payload["metadata"] == {
        "channel": "mobile",
        "corridor": "AU-US",
    }
    assert payload["version"] == 1


def test_instruction_canonical_dict_preserves_currencies() -> None:
    payload = instruction().canonical_dict()

    assert "AUD" in str(
        payload["requested_source_amount"]
    )
    assert "USD" in str(
        payload["expected_destination_amount"]
    )


def test_instruction_canonical_dict_is_fresh() -> None:
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
        first["beneficiary_reference"]
        is not second["beneficiary_reference"]
    )
    assert (
        first["requested_source_amount"]
        is not second["requested_source_amount"]
    )
    assert (
        first["expected_destination_amount"]
        is not second["expected_destination_amount"]
    )
    assert first["metadata"] is not second["metadata"]


def test_instruction_contains_no_execution_authority() -> None:
    names = {
        name
        for name in dir(TransferInstruction)
        if not name.startswith("__")
    }

    for forbidden in (
        "authorize_funds",
        "reserve_funds",
        "debit",
        "credit",
        "post",
        "settle",
        "execute",
        "send",
        "submit_to_provider",
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


def test_instruction_fields_contain_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(TransferInstruction)
    }

    for forbidden in (
        "wallet_repository",
        "ledger",
        "journal",
        "settlement_engine",
        "provider_client",
        "http_client",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names


def test_instruction_domain_is_exported_from_domain() -> None:
    import afritech.novapay.domain as domain

    for symbol in (
        "TransferFundingReference",
        "TransferBeneficiaryReference",
        "TransferInstructionId",
        "TransferInstructionMetadata",
        "TransferInstruction",
    ):
        assert hasattr(domain, symbol)
