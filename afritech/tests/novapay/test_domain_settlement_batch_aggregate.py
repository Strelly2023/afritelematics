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
    SettlementBatch,
    SettlementBatchId,
    SettlementBatchStatus,
    SettlementBatchType,
    SettlementMetadata,
    SettlementParticipant,
    SettlementReference,
    SettlementWindow,
)


OPEN_AT = datetime(
    2026,
    8,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)

CLOSE_AT = OPEN_AT + timedelta(hours=4)
CUTOFF_AT = OPEN_AT + timedelta(hours=3)


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


def money(amount: str, code: str = "AUD") -> Money:
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


def settlement_window() -> SettlementWindow:
    return SettlementWindow(
        opens_at=OPEN_AT,
        closes_at=CLOSE_AT,
        cutoff_at=CUTOFF_AT,
        timezone_name="Australia/Melbourne",
    )


def participant(
    identifier: str,
    *,
    currency_code: str = "AUD",
    jurisdiction_code: str | None = "AU",
    participant_type: str = "settlement account",
) -> SettlementParticipant:
    return SettlementParticipant.create(
        participant_id=identifier,
        participant_type=participant_type,
        account_reference=f"account-{identifier}",
        currency_code=currency_code,
        jurisdiction_code=jurisdiction_code,
        provider_code=f"provider-{identifier}",
    )


def reference(
    identifier: str,
    *,
    reference_type: str = "remittance",
) -> SettlementReference:
    return SettlementReference.create(
        reference_type=reference_type,
        reference_id=identifier,
    )


def create_batch(**overrides: Any) -> SettlementBatch:
    values: dict[str, Any] = {
        "batch_id": "settlement-batch-001",
        "batch_type": "netting",
        "window": settlement_window(),
        "settlement_currency_code": "AUD",
        "gross_amount": money("1000.00"),
        "net_amount": money("950.00"),
        "participants": (
            participant("participant-au"),
            participant(
                "participant-bdi",
                jurisdiction_code="BDI",
                participant_type="provider",
            ),
        ),
        "references": (
            reference("remittance-001"),
            reference(
                "transfer-001",
                reference_type="transfer",
            ),
        ),
        "entry_count": 2,
        "created_at": OPEN_AT,
        "metadata": {
            "settlement_version": "v1",
            "source_system": "novapay",
        },
    }

    values.update(overrides)
    return SettlementBatch.create(**values)


def construct_batch(**overrides: Any) -> SettlementBatch:
    values: dict[str, Any] = {
        "batch_id": SettlementBatchId.of(
            "settlement-batch-001"
        ),
        "batch_type": SettlementBatchType.NETTING,
        "status": SettlementBatchStatus.DRAFT,
        "window": settlement_window(),
        "settlement_currency_code": "AUD",
        "gross_amount": money("1000.00"),
        "net_amount": money("950.00"),
        "participants": (
            participant("participant-au"),
            participant(
                "participant-bdi",
                jurisdiction_code="BDI",
            ),
        ),
        "references": (
            reference("remittance-001"),
            reference(
                "transfer-001",
                reference_type="transfer",
            ),
        ),
        "entry_count": 2,
        "created_at": OPEN_AT,
        "updated_at": OPEN_AT,
        "version": 1,
        "metadata": SettlementMetadata.of(
            {
                "settlement_version": "v1",
            }
        ),
    }

    values.update(overrides)
    return SettlementBatch(**values)


def test_aggregate_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementBatch)
    } == {
        "batch_id",
        "batch_type",
        "status",
        "window",
        "settlement_currency_code",
        "gross_amount",
        "net_amount",
        "participants",
        "references",
        "entry_count",
        "created_at",
        "updated_at",
        "version",
        "metadata",
    }


def test_factory_defaults() -> None:
    value = create_batch()

    assert value.batch_id == SettlementBatchId.of(
        "settlement-batch-001"
    )
    assert value.batch_type is SettlementBatchType.NETTING
    assert value.status is SettlementBatchStatus.DRAFT
    assert value.version == 1
    assert value.created_at == OPEN_AT
    assert value.updated_at == OPEN_AT


def test_factory_normalizes_inputs() -> None:
    value = create_batch(
        batch_type="net",
        settlement_currency_code="aud",
        participants=[
            participant("participant-001"),
        ],
        references=[
            reference("remittance-001"),
        ],
        entry_count=1,
    )

    assert value.batch_type is SettlementBatchType.NETTING
    assert value.settlement_currency_code == "AUD"
    assert isinstance(value.participants, tuple)
    assert isinstance(value.references, tuple)


def test_direct_construction_normalizes_inputs() -> None:
    value = SettlementBatch(
        batch_id="settlement-batch-001",
        batch_type="daily batch",
        status="open",
        window=settlement_window(),
        settlement_currency_code="aud",
        gross_amount=money("100.00"),
        net_amount=money("90.00"),
        participants=[
            participant("participant-001"),
        ],
        references=[
            reference("remittance-001"),
        ],
        entry_count=1,
        created_at=OPEN_AT,
        updated_at=OPEN_AT,
        version=1,
        metadata={
            "source_system": "novapay",
        },
    )

    assert value.batch_id == SettlementBatchId.of(
        "settlement-batch-001"
    )
    assert value.batch_type is SettlementBatchType.DAILY
    assert value.status is SettlementBatchStatus.OPEN
    assert value.settlement_currency_code == "AUD"
    assert isinstance(value.participants, tuple)
    assert isinstance(value.references, tuple)
    assert isinstance(value.metadata, SettlementMetadata)


def test_canonical_money_objects_are_preserved() -> None:
    gross = money("1000.00")
    net = money("950.00")

    value = create_batch(
        gross_amount=gross,
        net_amount=net,
    )

    assert value.gross_amount is gross
    assert value.net_amount is net


def test_amount_classification_properties() -> None:
    value = create_batch()

    assert value.gross_amount_value == Decimal("1000.00")
    assert value.net_amount_value == Decimal("950.00")
    assert value.difference_amount_value == Decimal("50.00")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (SettlementBatchStatus.DRAFT, False),
        (SettlementBatchStatus.OPEN, False),
        (SettlementBatchStatus.VALIDATED, False),
        (SettlementBatchStatus.READY, False),
        (SettlementBatchStatus.PROCESSING, False),
        (SettlementBatchStatus.COMPLETE, True),
        (
            SettlementBatchStatus.PARTIALLY_COMPLETE,
            True,
        ),
        (SettlementBatchStatus.FAILURE, True),
        (SettlementBatchStatus.CANCELED, True),
        (SettlementBatchStatus.EXPIRED, True),
        (SettlementBatchStatus.RECONCILED, True),
    ],
)
def test_terminal_state_classification(
    status: SettlementBatchStatus,
    expected: bool,
) -> None:
    value = construct_batch(status=status)

    assert value.is_terminal is expected


def test_cross_jurisdictional_classification() -> None:
    value = create_batch()

    assert value.is_cross_jurisdictional is True


def test_single_jurisdiction_is_not_cross_jurisdictional() -> None:
    value = create_batch(
        participants=(
            participant("participant-001"),
            participant("participant-002"),
        ),
    )

    assert value.is_cross_jurisdictional is False


def test_missing_jurisdictions_are_ignored() -> None:
    value = create_batch(
        participants=(
            participant(
                "participant-001",
                jurisdiction_code=None,
            ),
            participant(
                "participant-002",
                jurisdiction_code=None,
            ),
        ),
    )

    assert value.is_cross_jurisdictional is False


def test_empty_batch_classification() -> None:
    value = create_batch(
        participants=(),
        references=(),
        entry_count=0,
        gross_amount=money("0"),
        net_amount=money("0"),
    )

    assert value.is_empty is True
    assert value.participant_count == 0
    assert value.reference_count == 0


def test_non_empty_batch_classification() -> None:
    value = create_batch()

    assert value.is_empty is False
    assert value.participant_count == 2
    assert value.reference_count == 2


def test_participant_order_is_preserved() -> None:
    first = participant("participant-001")
    second = participant("participant-002")

    value = create_batch(
        participants=(first, second),
    )

    assert value.participants == (first, second)


def test_reference_order_is_preserved() -> None:
    first = reference("transfer-001", reference_type="transfer")
    second = reference("remittance-001")

    value = create_batch(
        references=(first, second),
        entry_count=2,
    )

    assert value.references == (first, second)


def test_aggregate_is_immutable() -> None:
    value = create_batch()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        value.status = (  # type: ignore[misc]
            SettlementBatchStatus.OPEN
        )


def test_nested_collections_are_immutable_tuples() -> None:
    value = create_batch()

    assert isinstance(value.participants, tuple)
    assert isinstance(value.references, tuple)

    with pytest.raises(AttributeError):
        value.participants.append(  # type: ignore[attr-defined]
            participant("participant-new")
        )


def test_metadata_is_deeply_immutable() -> None:
    value = create_batch(
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


def test_canonical_serialization() -> None:
    value = create_batch()

    payload = value.canonical_dict()

    assert payload["batch_id"] == "settlement-batch-001"
    assert payload["batch_type"] == "netting"
    assert payload["status"] == "draft"
    assert payload["settlement_currency_code"] == "AUD"
    assert payload["entry_count"] == 2
    assert payload["participant_count"] == 2
    assert payload["reference_count"] == 2
    assert payload["created_at"] == OPEN_AT.isoformat()
    assert payload["updated_at"] == OPEN_AT.isoformat()
    assert payload["version"] == 1
    assert len(payload["participants"]) == 2
    assert len(payload["references"]) == 2
    assert payload["metadata"] == {
        "settlement_version": "v1",
        "source_system": "novapay",
    }


def test_canonical_serialization_preserves_money() -> None:
    value = create_batch()

    payload = value.canonical_dict()

    assert isinstance(payload["gross_amount"], dict)
    assert isinstance(payload["net_amount"], dict)

    gross_payload = payload["gross_amount"]
    net_payload = payload["net_amount"]

    assert gross_payload != {}
    assert net_payload != {}


def test_canonical_serialization_is_fresh() -> None:
    value = create_batch()

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


def test_serialized_participant_payloads_are_fresh() -> None:
    value = create_batch()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert (
        first["participants"][0]
        is not second["participants"][0]
    )


def test_serialized_reference_payloads_are_fresh() -> None:
    value = create_batch()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert (
        first["references"][0]
        is not second["references"][0]
    )


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1", "-1000"],
)
def test_rejects_negative_gross_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="gross amount must not be negative",
    ):
        create_batch(
            gross_amount=money(amount),
        )


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1", "-1000"],
)
def test_rejects_negative_net_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="net amount must not be negative",
    ):
        create_batch(
            net_amount=money(amount),
        )


def test_rejects_net_amount_above_gross_amount() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed gross amount",
    ):
        create_batch(
            gross_amount=money("100.00"),
            net_amount=money("100.01"),
        )


def test_allows_net_amount_equal_to_gross_amount() -> None:
    value = create_batch(
        gross_amount=money("100.00"),
        net_amount=money("100.00"),
    )

    assert value.difference_amount_value == Decimal("0.00")


def test_rejects_gross_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="gross amount currency",
    ):
        create_batch(
            gross_amount=money("1000.00", "USD"),
        )


def test_rejects_net_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="net amount currency",
    ):
        create_batch(
            net_amount=money("950.00", "USD"),
        )


def test_rejects_invalid_settlement_currency() -> None:
    with pytest.raises(
        ValueError,
        match="three-letter",
    ):
        create_batch(
            settlement_currency_code="AU",
        )


def test_rejects_participant_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="participant currency",
    ):
        create_batch(
            participants=(
                participant(
                    "participant-usd",
                    currency_code="USD",
                ),
            ),
        )


def test_rejects_duplicate_participant_ids() -> None:
    first = participant("participant-001")
    second = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="provider",
        account_reference="different-account",
        currency_code="AUD",
        jurisdiction_code="BDI",
    )

    with pytest.raises(
        ValueError,
        match="participant ids must be unique",
    ):
        create_batch(
            participants=(first, second),
        )


def test_rejects_non_participant_values() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementParticipant",
    ):
        create_batch(
            participants=("participant-001",),
        )


def test_rejects_non_iterable_participants() -> None:
    with pytest.raises(
        TypeError,
        match="participants must be iterable",
    ):
        create_batch(
            participants=1,
        )


def test_rejects_duplicate_references() -> None:
    duplicate = reference("remittance-001")

    with pytest.raises(
        ValueError,
        match="references must be unique",
    ):
        create_batch(
            references=(duplicate, duplicate),
            entry_count=2,
        )


def test_rejects_non_reference_values() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementReference",
    ):
        create_batch(
            references=("remittance-001",),
            entry_count=1,
        )


def test_rejects_non_iterable_references() -> None:
    with pytest.raises(
        TypeError,
        match="references must be iterable",
    ):
        create_batch(
            references=1,
        )


def test_rejects_entry_count_below_reference_count() -> None:
    with pytest.raises(
        ValueError,
        match="lower than reference count",
    ):
        create_batch(
            references=(
                reference("remittance-001"),
                reference(
                    "transfer-001",
                    reference_type="transfer",
                ),
            ),
            entry_count=1,
        )


@pytest.mark.parametrize(
    "entry_count",
    [-1, -100],
)
def test_rejects_negative_entry_count(
    entry_count: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_batch(
            references=(),
            entry_count=entry_count,
        )


@pytest.mark.parametrize(
    "entry_count",
    [True, False, "1", 1.5, None],
)
def test_rejects_invalid_entry_count_type(
    entry_count: object,
) -> None:
    with pytest.raises(TypeError):
        create_batch(
            references=(),
            entry_count=entry_count,
        )


def test_allows_entry_count_above_reference_count() -> None:
    value = create_batch(
        references=(
            reference("remittance-001"),
        ),
        entry_count=10,
    )

    assert value.entry_count == 10
    assert value.reference_count == 1


def test_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        create_batch(
            created_at=OPEN_AT.replace(tzinfo=None),
        )


def test_rejects_naive_updated_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        construct_batch(
            updated_at=OPEN_AT.replace(tzinfo=None),
        )


def test_rejects_updated_at_before_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="must not precede created_at",
    ):
        construct_batch(
            updated_at=OPEN_AT - timedelta(seconds=1),
        )


def test_allows_updated_at_equal_to_created_at() -> None:
    value = construct_batch(
        updated_at=OPEN_AT,
    )

    assert value.updated_at == value.created_at


def test_rejects_creation_after_window_close() -> None:
    with pytest.raises(
        ValueError,
        match="after the settlement window closes",
    ):
        create_batch(
            created_at=CLOSE_AT + timedelta(seconds=1),
        )


def test_allows_creation_at_window_close() -> None:
    value = create_batch(
        created_at=CLOSE_AT,
    )

    assert value.created_at == CLOSE_AT


@pytest.mark.parametrize(
    "version",
    [0, -1, -100],
)
def test_rejects_invalid_version_value(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        construct_batch(version=version)


@pytest.mark.parametrize(
    "version",
    [True, False, "1", 1.5, None],
)
def test_rejects_invalid_version_type(
    version: object,
) -> None:
    with pytest.raises(TypeError):
        construct_batch(version=version)


def test_rejects_invalid_window_type() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementWindow",
    ):
        create_batch(
            window="invalid-window",
        )


def test_rejects_invalid_gross_money_type() -> None:
    with pytest.raises(
        TypeError,
        match="gross amount must be Money",
    ):
        create_batch(
            gross_amount=Decimal("1000.00"),
        )


def test_rejects_invalid_net_money_type() -> None:
    with pytest.raises(
        TypeError,
        match="net amount must be Money",
    ):
        create_batch(
            net_amount=Decimal("950.00"),
        )


def test_sensitive_metadata_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        create_batch(
            metadata={
                "authorization": "secret",
            }
        )


def test_aggregate_remains_internal() -> None:
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


def test_aggregate_lifecycle_method_contract() -> None:
    required_methods = (
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
    )

    for method_name in required_methods:
        assert hasattr(
            SettlementBatch,
            method_name,
        )

    for forbidden in (
        "authorize",
        "execute",
        "settle",
        "submit_to_provider",
        "post_entry",
        "save",
        "persist",
    ):
        assert not hasattr(
            SettlementBatch,
            forbidden,
        )


def test_aggregate_has_no_operational_authority() -> None:
    names = {
        name
        for name in dir(SettlementBatch)
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
        "add_entry",
        "remove_entry",
    ):
        assert forbidden not in names


def test_aggregate_has_no_runtime_dependencies() -> None:
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


def test_module_all_contract_includes_aggregate() -> None:
    assert "SettlementBatch" in settlement_batch.__all__
    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )
    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )
