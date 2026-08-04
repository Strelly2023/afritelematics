from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest

import afritech.novapay.domain.settlement_batch as settlement_batch
from afritech.novapay.domain.currency import Currency
from afritech.novapay.domain.money import Money
from afritech.novapay.domain.settlement_batch import (
    SettlementBatchId,
    SettlementEntry,
    SettlementEntryId,
    SettlementEntryStatus,
    SettlementInstruction,
    SettlementInstructionId,
    SettlementInstructionMetadata,
    SettlementMetadata,
    SettlementParticipantId,
    SettlementReference,
)


REQUESTED_AT = datetime(
    2026,
    8,
    4,
    2,
    50,
    tzinfo=timezone.utc,
)

EFFECTIVE_AT = REQUESTED_AT + timedelta(minutes=5)
EXPIRES_AT = EFFECTIVE_AT + timedelta(hours=1)


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


def reference(
    identifier: str = "remittance-001",
    *,
    reference_type: str = "remittance",
) -> SettlementReference:
    return SettlementReference.create(
        reference_type=reference_type,
        reference_id=identifier,
    )


def create_entry(**overrides: Any) -> SettlementEntry:
    values: dict[str, Any] = {
        "entry_id": "settlement-entry-001",
        "batch_id": "settlement-batch-001",
        "amount": money("250.00"),
        "settlement_currency_code": "AUD",
        "source_participant_id": "participant-source",
        "destination_participant_id": (
            "participant-destination"
        ),
        "reference": reference(),
        "created_at": REQUESTED_AT,
        "metadata": {
            "source_system": "novapay",
            "entry_version": "v1",
        },
    }

    values.update(overrides)
    return SettlementEntry.create(**values)


def construct_entry(**overrides: Any) -> SettlementEntry:
    values: dict[str, Any] = {
        "entry_id": SettlementEntryId.of(
            "settlement-entry-001"
        ),
        "batch_id": SettlementBatchId.of(
            "settlement-batch-001"
        ),
        "status": SettlementEntryStatus.PENDING,
        "amount": money("250.00"),
        "settlement_currency_code": "AUD",
        "source_participant_id": (
            SettlementParticipantId.of(
                "participant-source"
            )
        ),
        "destination_participant_id": (
            SettlementParticipantId.of(
                "participant-destination"
            )
        ),
        "reference": reference(),
        "created_at": REQUESTED_AT,
        "metadata": SettlementMetadata.of(
            {
                "source_system": "novapay",
            }
        ),
    }

    values.update(overrides)
    return SettlementEntry(**values)


def create_instruction(
    **overrides: Any,
) -> SettlementInstruction:
    values: dict[str, Any] = {
        "instruction_id": "settlement-instruction-001",
        "batch_id": "settlement-batch-001",
        "source_participant_id": "participant-source",
        "destination_participant_id": (
            "participant-destination"
        ),
        "amount": money("250.00"),
        "settlement_currency_code": "AUD",
        "reference": reference(),
        "requested_at": REQUESTED_AT,
        "effective_at": EFFECTIVE_AT,
        "expires_at": EXPIRES_AT,
        "metadata": {
            "source_system": "novapay",
            "instruction_version": "v1",
        },
    }

    values.update(overrides)
    return SettlementInstruction.create(**values)


def construct_instruction(
    **overrides: Any,
) -> SettlementInstruction:
    values: dict[str, Any] = {
        "instruction_id": SettlementInstructionId.of(
            "settlement-instruction-001"
        ),
        "batch_id": SettlementBatchId.of(
            "settlement-batch-001"
        ),
        "source_participant_id": (
            SettlementParticipantId.of(
                "participant-source"
            )
        ),
        "destination_participant_id": (
            SettlementParticipantId.of(
                "participant-destination"
            )
        ),
        "amount": money("250.00"),
        "settlement_currency_code": "AUD",
        "reference": reference(),
        "requested_at": REQUESTED_AT,
        "effective_at": EFFECTIVE_AT,
        "expires_at": EXPIRES_AT,
        "metadata": SettlementInstructionMetadata.of(
            {
                "source_system": "novapay",
            }
        ),
    }

    values.update(overrides)
    return SettlementInstruction(**values)


def test_entry_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementEntry)
    } == {
        "entry_id",
        "batch_id",
        "status",
        "amount",
        "settlement_currency_code",
        "source_participant_id",
        "destination_participant_id",
        "reference",
        "created_at",
        "metadata",
    }


def test_instruction_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementInstruction)
    } == {
        "instruction_id",
        "batch_id",
        "source_participant_id",
        "destination_participant_id",
        "amount",
        "settlement_currency_code",
        "reference",
        "requested_at",
        "effective_at",
        "expires_at",
        "metadata",
    }


def test_instruction_metadata_field_contract() -> None:
    assert {
        item.name
        for item in fields(
            SettlementInstructionMetadata
        )
    } == {"values"}


def test_entry_factory_defaults() -> None:
    value = create_entry()

    assert value.entry_id == SettlementEntryId.of(
        "settlement-entry-001"
    )
    assert value.batch_id == SettlementBatchId.of(
        "settlement-batch-001"
    )
    assert value.status is SettlementEntryStatus.PENDING


def test_entry_factory_normalizes_currency() -> None:
    value = create_entry(
        settlement_currency_code="aud",
    )

    assert value.settlement_currency_code == "AUD"


def test_entry_direct_construction_normalizes() -> None:
    value = SettlementEntry(
        entry_id="settlement-entry-001",
        batch_id="settlement-batch-001",
        status="included",
        amount=money("250.00"),
        settlement_currency_code="aud",
        source_participant_id="participant-source",
        destination_participant_id=(
            "participant-destination"
        ),
        reference=reference(),
        created_at=REQUESTED_AT,
        metadata={"source_system": "novapay"},
    )

    assert value.status is SettlementEntryStatus.INCLUDED
    assert value.settlement_currency_code == "AUD"
    assert isinstance(value.metadata, SettlementMetadata)


def test_entry_preserves_money_identity() -> None:
    amount = money("250.00")

    value = create_entry(amount=amount)

    assert value.amount is amount


def test_entry_preserves_reference_identity() -> None:
    entry_reference = reference()

    value = create_entry(reference=entry_reference)

    assert value.reference is entry_reference


def test_entry_amount_value() -> None:
    value = create_entry(
        amount=money("250.50"),
    )

    assert value.amount_value == Decimal("250.50")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (SettlementEntryStatus.PENDING, False),
        (SettlementEntryStatus.VALIDATED, False),
        (SettlementEntryStatus.INCLUDED, False),
        (SettlementEntryStatus.PROCESSING, False),
        (SettlementEntryStatus.COMPLETE, True),
        (SettlementEntryStatus.FAILURE, True),
        (SettlementEntryStatus.EXCLUDED, True),
        (SettlementEntryStatus.REVERSED, True),
    ],
)
def test_entry_terminal_classification(
    status: SettlementEntryStatus,
    expected: bool,
) -> None:
    value = construct_entry(status=status)

    assert value.is_terminal is expected


def test_entry_is_immutable() -> None:
    value = create_entry()

    with pytest.raises(FrozenInstanceError):
        value.status = (  # type: ignore[misc]
            SettlementEntryStatus.COMPLETE
        )


def test_entry_metadata_is_immutable() -> None:
    value = create_entry(
        metadata={
            "nested": {
                "source": "novapay",
            }
        }
    )

    assert isinstance(
        value.metadata.values,
        MappingProxyType,
    )

    nested = value.metadata.values["nested"]

    assert isinstance(nested, MappingProxyType)

    with pytest.raises(TypeError):
        nested["source"] = "changed"  # type: ignore[index]


def test_entry_canonical_serialization() -> None:
    value = create_entry()

    payload = value.canonical_dict()

    assert payload["entry_id"] == "settlement-entry-001"
    assert payload["batch_id"] == "settlement-batch-001"
    assert payload["status"] == "pending"
    assert payload["settlement_currency_code"] == "AUD"
    assert payload["source_participant_id"] == (
        "participant-source"
    )
    assert payload["destination_participant_id"] == (
        "participant-destination"
    )
    assert payload["created_at"] == (
        REQUESTED_AT.isoformat()
    )
    assert payload["metadata"] == {
        "entry_version": "v1",
        "source_system": "novapay",
    }


def test_entry_serialization_is_fresh() -> None:
    value = create_entry()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["amount"] is not second["amount"]
    assert first["reference"] is not second["reference"]
    assert first["metadata"] is not second["metadata"]


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1.00", "-100.00"],
)
def test_entry_rejects_negative_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_entry(
            amount=money(amount),
        )


def test_entry_allows_zero_amount() -> None:
    value = create_entry(
        amount=money("0.00"),
    )

    assert value.amount_value == Decimal("0.00")


def test_entry_rejects_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="must match settlement currency",
    ):
        create_entry(
            amount=money("250.00", "USD"),
        )


def test_entry_rejects_empty_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        create_entry(
            settlement_currency_code="",
        )


def test_entry_rejects_overlength_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 3 characters",
    ):
        create_entry(
            settlement_currency_code="AUDD",
        )


@pytest.mark.parametrize(
    "currency_code",
    ["AU", "12A"],
)
def test_entry_rejects_malformed_currency_code(
    currency_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="three-letter",
    ):
        create_entry(
            settlement_currency_code=currency_code,
        )


def test_entry_rejects_same_participant_endpoints() -> None:
    with pytest.raises(
        ValueError,
        match="must be different",
    ):
        create_entry(
            source_participant_id="participant-one",
            destination_participant_id="participant-one",
        )


def test_entry_rejects_invalid_reference_type() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementReference",
    ):
        create_entry(
            reference="invalid-reference",
        )


def test_entry_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        create_entry(
            created_at=REQUESTED_AT.replace(
                tzinfo=None
            )
        )


def test_entry_rejects_invalid_money_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        create_entry(
            amount=Decimal("250.00"),
        )


def test_entry_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        create_entry(
            metadata={
                "authorization": "secret",
            }
        )


def test_instruction_metadata_defaults_empty() -> None:
    value = SettlementInstructionMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_instruction_metadata_preserves_instance() -> None:
    value = SettlementInstructionMetadata.of(
        {"source_system": "novapay"}
    )

    assert (
        SettlementInstructionMetadata.of(value)
        is value
    )


def test_instruction_metadata_accepts_settlement_metadata() -> None:
    source = SettlementMetadata.of(
        {"source_system": "novapay"}
    )

    value = SettlementInstructionMetadata.of(source)

    assert value.values == source.values


def test_instruction_metadata_normalization() -> None:
    value = SettlementInstructionMetadata.of(
        {
            "Instruction Version": "v1",
            "Source-System": "novapay",
            "Attempt": 1,
            "Tags": ["settlement", "aud"],
            "Nested": {
                "Provider Reference": "provider-001",
            },
        }
    )

    assert value.values == {
        "attempt": 1,
        "instruction_version": "v1",
        "nested": {
            "provider_reference": "provider-001",
        },
        "source_system": "novapay",
        "tags": (
            "settlement",
            "aud",
        ),
    }


def test_instruction_metadata_is_immutable() -> None:
    value = SettlementInstructionMetadata.of(
        {"source_system": "novapay"}
    )

    assert isinstance(
        value.values,
        MappingProxyType,
    )

    with pytest.raises(FrozenInstanceError):
        value.values = {}  # type: ignore[misc]

    with pytest.raises(TypeError):
        value.values["source_system"] = (  # type: ignore[index]
            "changed"
        )


def test_instruction_metadata_canonical_dict() -> None:
    value = SettlementInstructionMetadata.of(
        {
            "source_system": "novapay",
            "attempt": 1,
        }
    )

    assert value.canonical_dict() == {
        "attempt": 1,
        "source_system": "novapay",
    }


@pytest.mark.parametrize(
    "sensitive_key",
    [
        "access_token",
        "api_key",
        "authorization",
        "credential",
        "credentials",
        "password",
        "pin",
        "private_key",
        "secret",
        "security_code",
        "token",
        "provider_api_key",
    ],
)
def test_instruction_metadata_rejects_sensitive_keys(
    sensitive_key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        SettlementInstructionMetadata.of(
            {sensitive_key: "sensitive"}
        )


def test_instruction_factory_defaults_effective_at() -> None:
    value = create_instruction(
        effective_at=None,
    )

    assert value.effective_at == value.requested_at


def test_instruction_factory_normalizes_currency() -> None:
    value = create_instruction(
        settlement_currency_code="aud",
    )

    assert value.settlement_currency_code == "AUD"


def test_instruction_direct_construction_normalizes() -> None:
    value = SettlementInstruction(
        instruction_id="settlement-instruction-001",
        batch_id="settlement-batch-001",
        source_participant_id="participant-source",
        destination_participant_id=(
            "participant-destination"
        ),
        amount=money("250.00"),
        settlement_currency_code="aud",
        reference=reference(),
        requested_at=REQUESTED_AT,
        effective_at=EFFECTIVE_AT,
        expires_at=EXPIRES_AT,
        metadata={"source_system": "novapay"},
    )

    assert value.settlement_currency_code == "AUD"
    assert isinstance(
        value.metadata,
        SettlementInstructionMetadata,
    )


def test_instruction_preserves_money_identity() -> None:
    amount = money("250.00")

    value = create_instruction(amount=amount)

    assert value.amount is amount


def test_instruction_preserves_reference_identity() -> None:
    instruction_reference = reference()

    value = create_instruction(
        reference=instruction_reference,
    )

    assert value.reference is instruction_reference


def test_instruction_amount_value() -> None:
    value = create_instruction(
        amount=money("275.75"),
    )

    assert value.amount_value == Decimal("275.75")


def test_instruction_without_expiry_never_expires() -> None:
    value = create_instruction(
        expires_at=None,
    )

    assert value.expires_at is None
    assert value.is_expired(
        at=REQUESTED_AT + timedelta(days=365)
    ) is False


def test_instruction_expiry_boundary() -> None:
    value = create_instruction()

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
    value = create_instruction()

    offset_time = EXPIRES_AT.astimezone(
        timezone(timedelta(hours=10))
    )

    assert value.is_expired(at=offset_time) is True


def test_instruction_is_immutable() -> None:
    value = create_instruction()

    with pytest.raises(FrozenInstanceError):
        value.expires_at = None  # type: ignore[misc]


def test_instruction_canonical_serialization() -> None:
    value = create_instruction()

    payload = value.canonical_dict()

    assert payload["instruction_id"] == (
        "settlement-instruction-001"
    )
    assert payload["batch_id"] == "settlement-batch-001"
    assert payload["source_participant_id"] == (
        "participant-source"
    )
    assert payload["destination_participant_id"] == (
        "participant-destination"
    )
    assert payload["settlement_currency_code"] == "AUD"
    assert payload["requested_at"] == (
        REQUESTED_AT.isoformat()
    )
    assert payload["effective_at"] == (
        EFFECTIVE_AT.isoformat()
    )
    assert payload["expires_at"] == (
        EXPIRES_AT.isoformat()
    )
    assert payload["metadata"] == {
        "instruction_version": "v1",
        "source_system": "novapay",
    }


def test_instruction_serialization_without_expiry() -> None:
    value = create_instruction(
        expires_at=None,
    )

    assert value.canonical_dict()["expires_at"] is None


def test_instruction_serialization_is_fresh() -> None:
    value = create_instruction()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["amount"] is not second["amount"]
    assert first["reference"] is not second["reference"]
    assert first["metadata"] is not second["metadata"]


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1.00", "-100.00"],
)
def test_instruction_rejects_negative_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_instruction(
            amount=money(amount),
        )


def test_instruction_allows_zero_amount() -> None:
    value = create_instruction(
        amount=money("0.00"),
    )

    assert value.amount_value == Decimal("0.00")


def test_instruction_rejects_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="must match settlement currency",
    ):
        create_instruction(
            amount=money("250.00", "USD"),
        )


def test_instruction_rejects_empty_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        create_instruction(
            settlement_currency_code="",
        )


def test_instruction_rejects_overlength_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 3 characters",
    ):
        create_instruction(
            settlement_currency_code="AUDD",
        )


@pytest.mark.parametrize(
    "currency_code",
    ["AU", "12A"],
)
def test_instruction_rejects_malformed_currency_code(
    currency_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="three-letter",
    ):
        create_instruction(
            settlement_currency_code=currency_code,
        )


def test_instruction_rejects_same_endpoints() -> None:
    with pytest.raises(
        ValueError,
        match="must be different",
    ):
        create_instruction(
            source_participant_id="participant-one",
            destination_participant_id="participant-one",
        )


def test_instruction_rejects_effective_before_requested() -> None:
    with pytest.raises(
        ValueError,
        match="must not precede requested_at",
    ):
        create_instruction(
            effective_at=REQUESTED_AT
            - timedelta(microseconds=1)
        )


def test_instruction_allows_effective_equal_requested() -> None:
    value = create_instruction(
        effective_at=REQUESTED_AT,
    )

    assert value.effective_at == value.requested_at


@pytest.mark.parametrize(
    "expires_at",
    [
        EFFECTIVE_AT,
        EFFECTIVE_AT - timedelta(microseconds=1),
    ],
)
def test_instruction_rejects_invalid_expiry(
    expires_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be after effective_at",
    ):
        create_instruction(
            expires_at=expires_at,
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        (
            "requested_at",
            REQUESTED_AT.replace(tzinfo=None),
        ),
        (
            "effective_at",
            EFFECTIVE_AT.replace(tzinfo=None),
        ),
        (
            "expires_at",
            EXPIRES_AT.replace(tzinfo=None),
        ),
    ],
)
def test_instruction_rejects_naive_datetimes(
    field_name: str,
    field_value: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        create_instruction(
            **{field_name: field_value}
        )


def test_instruction_expiry_check_rejects_naive_time() -> None:
    value = create_instruction()

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        value.is_expired(
            at=REQUESTED_AT.replace(tzinfo=None)
        )


def test_instruction_rejects_invalid_reference_type() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementReference",
    ):
        create_instruction(
            reference="invalid-reference",
        )


def test_instruction_rejects_invalid_money_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be Money",
    ):
        create_instruction(
            amount=Decimal("250.00"),
        )


def test_instruction_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        create_instruction(
            metadata={
                "authorization": "secret",
            }
        )


def test_module_all_contract_includes_section_4a() -> None:
    for symbol in (
        "SettlementEntry",
        "SettlementInstruction",
        "SettlementInstructionMetadata",
    ):
        assert symbol in settlement_batch.__all__

    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )

    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )


def test_section_4a_domain_remains_internal() -> None:
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


def test_entry_has_no_lifecycle_methods() -> None:
    for method_name in (
        "validate",
        "include",
        "mark_processing",
        "complete",
        "fail",
        "exclude",
        "reverse",
        "update_metadata",
    ):
        assert not hasattr(
            SettlementEntry,
            method_name,
        )


def test_instruction_has_no_execution_methods() -> None:
    for method_name in (
        "validate",
        "authorize",
        "execute",
        "submit",
        "submit_to_provider",
        "settle",
        "complete",
        "fail",
        "cancel",
        "reverse",
    ):
        assert not hasattr(
            SettlementInstruction,
            method_name,
        )


def test_section_4a_has_no_operational_authority() -> None:
    for value_type in (
        SettlementEntry,
        SettlementInstruction,
        SettlementInstructionMetadata,
    ):
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "reserve",
            "reserve_funds",
            "debit",
            "credit",
            "post",
            "post_entry",
            "execute",
            "settle",
            "reconcile",
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


@pytest.mark.parametrize(
    "value_type",
    [
        SettlementEntry,
        SettlementInstruction,
    ],
)
def test_section_4a_has_no_runtime_dependencies(
    value_type: type,
) -> None:
    field_names = {
        item.name
        for item in fields(value_type)
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
