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
    SettlementBatchStatus,
    SettlementEntryId,
    SettlementFailure,
    SettlementMetadata,
    SettlementResult,
    SettlementSummary,
)


COMPLETED_AT = datetime(
    2026,
    8,
    4,
    5,
    0,
    tzinfo=timezone.utc,
)

OPENED_AT = COMPLETED_AT - timedelta(hours=1)


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


def money(
    amount: str,
    code: str = "AUD",
) -> Money:
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


def failure(
    *,
    code: str = "provider_timeout",
    message: str = "Provider did not respond",
    entry_id: str | None = "entry-001",
    retryable: bool = True,
    occurred_at: datetime = COMPLETED_AT,
    metadata: object = None,
) -> SettlementFailure:
    return SettlementFailure.create(
        failure_code=code,
        message=message,
        occurred_at=occurred_at,
        entry_id=entry_id,
        retryable=retryable,
        metadata=(
            {"provider_code": "provider_one"}
            if metadata is None
            else metadata
        ),
    )


def result(
    **overrides: Any,
) -> SettlementResult:
    values: dict[str, Any] = {
        "batch_id": "settlement-batch-001",
        "status": SettlementBatchStatus.PARTIALLY_COMPLETE,
        "gross_amount": money("1000.00"),
        "net_amount": money("950.00"),
        "settlement_currency_code": "AUD",
        "successful_entry_count": 8,
        "failed_entry_count": 1,
        "excluded_entry_count": 1,
        "failures": (failure(),),
        "completed_at": COMPLETED_AT,
        "metadata": {
            "source_system": "novapay",
            "result_version": "v1",
        },
    }

    values.update(overrides)
    return SettlementResult(**values)


def summary(
    **overrides: Any,
) -> SettlementSummary:
    values: dict[str, Any] = {
        "batch_id": "settlement-batch-001",
        "status": SettlementBatchStatus.COMPLETE,
        "settlement_currency_code": "AUD",
        "gross_amount": money("1000.00"),
        "net_amount": money("950.00"),
        "total_entry_count": 10,
        "successful_entry_count": 9,
        "failed_entry_count": 0,
        "excluded_entry_count": 1,
        "participant_count": 2,
        "opened_at": OPENED_AT,
        "closed_at": COMPLETED_AT,
        "metadata": {
            "source_system": "novapay",
            "summary_version": "v1",
        },
    }

    values.update(overrides)
    return SettlementSummary(**values)


def test_failure_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementFailure)
    } == {
        "failure_code",
        "message",
        "occurred_at",
        "entry_id",
        "retryable",
        "metadata",
    }


def test_result_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementResult)
    } == {
        "batch_id",
        "status",
        "gross_amount",
        "net_amount",
        "settlement_currency_code",
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
        "failures",
        "completed_at",
        "metadata",
    }


def test_summary_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementSummary)
    } == {
        "batch_id",
        "status",
        "settlement_currency_code",
        "gross_amount",
        "net_amount",
        "total_entry_count",
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
        "participant_count",
        "opened_at",
        "closed_at",
        "metadata",
    }


def test_failure_factory_normalizes_values() -> None:
    value = failure(
        code="Provider Timeout",
        message="  Provider   did not respond  ",
    )

    assert value.failure_code == "provider_timeout"
    assert value.message == "Provider did not respond"
    assert value.entry_id == SettlementEntryId.of(
        "entry-001"
    )
    assert value.retryable is True


def test_failure_allows_batch_level_failure() -> None:
    value = failure(entry_id=None)

    assert value.entry_id is None


def test_failure_metadata_is_immutable() -> None:
    value = failure(
        metadata={
            "nested": {
                "provider": "provider_one",
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
        nested["provider"] = "changed"  # type: ignore[index]


def test_failure_is_immutable() -> None:
    value = failure()

    with pytest.raises(FrozenInstanceError):
        value.retryable = False  # type: ignore[misc]


def test_failure_canonical_serialization() -> None:
    value = failure()

    assert value.canonical_dict() == {
        "failure_code": "provider_timeout",
        "message": "Provider did not respond",
        "occurred_at": COMPLETED_AT.isoformat(),
        "entry_id": "entry-001",
        "retryable": True,
        "metadata": {
            "provider_code": "provider_one",
        },
    }


def test_failure_serialization_is_fresh() -> None:
    value = failure()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["metadata"] is not second["metadata"]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("Provider Timeout", "provider_timeout"),
        ("provider-timeout", "provider_timeout"),
        ("PROVIDER_TIMEOUT", "provider_timeout"),
        (" provider timeout ", "provider_timeout"),
    ],
)
def test_failure_code_normalization(
    code: str,
    expected: str,
) -> None:
    assert failure(code=code).failure_code == expected


@pytest.mark.parametrize(
    "invalid_code",
    [
        "",
        "   ",
        "invalid?",
        None,
        1,
    ],
)
def test_failure_rejects_invalid_code(
    invalid_code: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        SettlementFailure.create(
            failure_code=invalid_code,
            message="Failure",
            occurred_at=COMPLETED_AT,
        )


@pytest.mark.parametrize(
    "invalid_message",
    [
        "",
        "   ",
        None,
        1,
    ],
)
def test_failure_rejects_invalid_message(
    invalid_message: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        SettlementFailure.create(
            failure_code="failure",
            message=invalid_message,
            occurred_at=COMPLETED_AT,
        )


def test_failure_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        failure(
            occurred_at=COMPLETED_AT.replace(
                tzinfo=None
            )
        )


@pytest.mark.parametrize(
    "retryable",
    [0, 1, "true", None],
)
def test_failure_rejects_non_boolean_retryable(
    retryable: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be boolean",
    ):
        SettlementFailure.create(
            failure_code="failure",
            message="Failure",
            occurred_at=COMPLETED_AT,
            retryable=retryable,  # type: ignore[arg-type]
        )


def test_failure_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        failure(
            metadata={
                "authorization": "secret",
            }
        )


def test_result_normalizes_identity_and_status() -> None:
    value = result(
        batch_id="batch-001",
        status="partially complete",
        settlement_currency_code="aud",
    )

    assert value.batch_id == SettlementBatchId.of(
        "batch-001"
    )

    assert (
        value.status
        is SettlementBatchStatus.PARTIALLY_COMPLETE
    )

    assert value.settlement_currency_code == "AUD"


def test_result_preserves_canonical_money_identity() -> None:
    gross = money("1000.00")
    net = money("950.00")

    value = result(
        gross_amount=gross,
        net_amount=net,
    )

    assert value.gross_amount is gross
    assert value.net_amount is net


def test_result_count_properties() -> None:
    value = result()

    assert value.successful_entry_count == 8
    assert value.failed_entry_count == 1
    assert value.excluded_entry_count == 1
    assert value.total_entry_count == 10


def test_result_amount_properties() -> None:
    value = result()

    assert value.gross_amount_value == Decimal("1000.00")
    assert value.net_amount_value == Decimal("950.00")
    assert value.difference_amount_value == Decimal("50.00")


def test_result_has_failures() -> None:
    assert result().has_failures is True


def test_complete_result_has_no_failures() -> None:
    value = result(
        status=SettlementBatchStatus.COMPLETE,
        successful_entry_count=10,
        failed_entry_count=0,
        excluded_entry_count=0,
        failures=(),
    )

    assert value.has_failures is False
    assert value.total_entry_count == 10


def test_failure_result_contract() -> None:
    value = result(
        status=SettlementBatchStatus.FAILURE,
        successful_entry_count=0,
        failed_entry_count=2,
        excluded_entry_count=0,
        failures=(
            failure(entry_id="entry-001"),
            failure(
                code="provider_rejected",
                entry_id="entry-002",
            ),
        ),
    )

    assert value.status is SettlementBatchStatus.FAILURE
    assert value.successful_entry_count == 0
    assert value.failed_entry_count == 2
    assert value.has_failures is True


def test_reconciled_result_contract() -> None:
    value = result(
        status=SettlementBatchStatus.RECONCILED,
    )

    assert value.status is SettlementBatchStatus.RECONCILED


def test_result_failures_are_immutable_tuple() -> None:
    value = result(
        failures=[failure()],
    )

    assert isinstance(value.failures, tuple)

    with pytest.raises(AttributeError):
        value.failures.append(  # type: ignore[attr-defined]
            failure(code="another_failure")
        )


def test_result_is_immutable() -> None:
    value = result()

    with pytest.raises(FrozenInstanceError):
        value.status = SettlementBatchStatus.COMPLETE  # type: ignore[misc]


def test_result_metadata_is_immutable() -> None:
    value = result(
        metadata={
            "nested": {
                "source": "novapay",
            }
        }
    )

    nested = value.metadata.values["nested"]

    assert isinstance(nested, MappingProxyType)

    with pytest.raises(TypeError):
        nested["source"] = "changed"  # type: ignore[index]


def test_result_canonical_serialization() -> None:
    value = result()

    payload = value.canonical_dict()

    assert payload["batch_id"] == "settlement-batch-001"
    assert payload["status"] == "partially_complete"
    assert payload["settlement_currency_code"] == "AUD"
    assert payload["successful_entry_count"] == 8
    assert payload["failed_entry_count"] == 1
    assert payload["excluded_entry_count"] == 1
    assert payload["total_entry_count"] == 10
    assert payload["completed_at"] == (
        COMPLETED_AT.isoformat()
    )
    assert len(payload["failures"]) == 1


def test_result_serialization_is_fresh() -> None:
    value = result()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["gross_amount"] is not second["gross_amount"]
    assert first["net_amount"] is not second["net_amount"]
    assert first["failures"] is not second["failures"]
    assert first["failures"][0] is not second["failures"][0]
    assert first["metadata"] is not second["metadata"]


@pytest.mark.parametrize(
    "status",
    [
        SettlementBatchStatus.DRAFT,
        SettlementBatchStatus.OPEN,
        SettlementBatchStatus.VALIDATED,
        SettlementBatchStatus.READY,
        SettlementBatchStatus.PROCESSING,
        SettlementBatchStatus.CANCELED,
        SettlementBatchStatus.EXPIRED,
    ],
)
def test_result_rejects_non_result_status(
    status: SettlementBatchStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be terminal",
    ):
        result(status=status)


def test_complete_result_rejects_failed_entries() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain failed entries",
    ):
        result(
            status=SettlementBatchStatus.COMPLETE,
            successful_entry_count=9,
            failed_entry_count=1,
        )


def test_failed_result_rejects_successful_entries() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain successful entries",
    ):
        result(
            status=SettlementBatchStatus.FAILURE,
            successful_entry_count=1,
            failed_entry_count=1,
        )


@pytest.mark.parametrize(
    (
        "successful_count",
        "failed_count",
    ),
    [
        (0, 1),
        (1, 0),
        (0, 0),
    ],
)
def test_partial_result_requires_success_and_failure(
    successful_count: int,
    failed_count: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must contain successful and failed entries",
    ):
        result(
            successful_entry_count=successful_count,
            failed_entry_count=failed_count,
            failures=(
                ()
                if failed_count == 0
                else (failure(),)
            ),
        )


def test_result_rejects_failure_count_below_failure_records() -> None:
    with pytest.raises(
        ValueError,
        match="must not be lower than failure count",
    ):
        result(
            failed_entry_count=1,
            failures=(
                failure(entry_id="entry-001"),
                failure(
                    code="provider_rejected",
                    entry_id="entry-002",
                ),
            ),
        )


def test_result_allows_failed_count_above_recorded_failures() -> None:
    value = result(
        failed_entry_count=2,
        failures=(failure(),),
    )

    assert value.failed_entry_count == 2
    assert len(value.failures) == 1


@pytest.mark.parametrize(
    "field_name",
    [
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
    ],
)
def test_result_rejects_negative_counts(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        result(**{field_name: -1})


@pytest.mark.parametrize(
    "field_name",
    [
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [True, "1", 1.5, None],
)
def test_result_rejects_invalid_count_types(
    field_name: str,
    invalid_value: object,
) -> None:
    with pytest.raises(TypeError):
        result(**{field_name: invalid_value})


def test_result_rejects_non_iterable_failures() -> None:
    with pytest.raises(
        TypeError,
        match="failures must be iterable",
    ):
        result(failures=1)


def test_result_rejects_invalid_failure_values() -> None:
    with pytest.raises(
        TypeError,
        match="SettlementFailure",
    ):
        result(failures=("failure",))


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1.00"],
)
def test_result_rejects_negative_gross_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        result(gross_amount=money(amount))


@pytest.mark.parametrize(
    "amount",
    ["-0.01", "-1.00"],
)
def test_result_rejects_negative_net_amount(
    amount: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        result(net_amount=money(amount))


def test_result_rejects_net_above_gross() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed gross amount",
    ):
        result(
            gross_amount=money("100.00"),
            net_amount=money("100.01"),
        )


def test_result_rejects_gross_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="gross amount currency",
    ):
        result(
            gross_amount=money("1000.00", "USD"),
        )


def test_result_rejects_net_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="net amount currency",
    ):
        result(
            net_amount=money("950.00", "USD"),
        )


def test_result_rejects_empty_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        result(settlement_currency_code="")


def test_result_rejects_overlength_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 3 characters",
    ):
        result(settlement_currency_code="AUDD")


@pytest.mark.parametrize(
    "currency_code",
    ["AU", "12A"],
)
def test_result_rejects_malformed_currency_code(
    currency_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="three-letter",
    ):
        result(settlement_currency_code=currency_code)


def test_result_rejects_naive_completed_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        result(
            completed_at=COMPLETED_AT.replace(
                tzinfo=None
            )
        )


def test_result_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        result(
            metadata={
                "authorization": "secret",
            }
        )


def test_summary_normalizes_identity_and_status() -> None:
    value = summary(
        batch_id="batch-001",
        status="complete",
        settlement_currency_code="aud",
    )

    assert value.batch_id == SettlementBatchId.of(
        "batch-001"
    )
    assert value.status is SettlementBatchStatus.COMPLETE
    assert value.settlement_currency_code == "AUD"


def test_summary_preserves_canonical_money_identity() -> None:
    gross = money("1000.00")
    net = money("950.00")

    value = summary(
        gross_amount=gross,
        net_amount=net,
    )

    assert value.gross_amount is gross
    assert value.net_amount is net


def test_summary_amount_properties() -> None:
    value = summary()

    assert value.gross_amount_value == Decimal("1000.00")
    assert value.net_amount_value == Decimal("950.00")
    assert value.difference_amount_value == Decimal("50.00")


def test_summary_success_rate() -> None:
    value = summary()

    assert value.success_rate == Decimal("0.9")


def test_summary_success_rate_precision() -> None:
    value = summary(
        total_entry_count=3,
        successful_entry_count=1,
        failed_entry_count=1,
        excluded_entry_count=1,
    )

    assert value.success_rate == (
        Decimal(1) / Decimal(3)
    )


def test_summary_zero_entry_success_rate() -> None:
    value = summary(
        total_entry_count=0,
        successful_entry_count=0,
        failed_entry_count=0,
        excluded_entry_count=0,
        participant_count=0,
        gross_amount=money("0.00"),
        net_amount=money("0.00"),
    )

    assert value.success_rate == Decimal("0")


def test_summary_allows_same_open_and_close_timestamp() -> None:
    value = summary(
        opened_at=COMPLETED_AT,
        closed_at=COMPLETED_AT,
    )

    assert value.opened_at == value.closed_at


def test_summary_is_immutable() -> None:
    value = summary()

    with pytest.raises(FrozenInstanceError):
        value.total_entry_count = 11  # type: ignore[misc]


def test_summary_metadata_is_immutable() -> None:
    value = summary(
        metadata={
            "nested": {
                "source": "novapay",
            }
        }
    )

    nested = value.metadata.values["nested"]

    assert isinstance(nested, MappingProxyType)

    with pytest.raises(TypeError):
        nested["source"] = "changed"  # type: ignore[index]


def test_summary_canonical_serialization() -> None:
    value = summary()

    payload = value.canonical_dict()

    assert payload["batch_id"] == "settlement-batch-001"
    assert payload["status"] == "complete"
    assert payload["settlement_currency_code"] == "AUD"
    assert payload["total_entry_count"] == 10
    assert payload["successful_entry_count"] == 9
    assert payload["failed_entry_count"] == 0
    assert payload["excluded_entry_count"] == 1
    assert payload["participant_count"] == 2
    assert payload["opened_at"] == OPENED_AT.isoformat()
    assert payload["closed_at"] == COMPLETED_AT.isoformat()
    assert payload["success_rate"] == "0.9"


def test_summary_serialization_is_fresh() -> None:
    value = summary()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["gross_amount"] is not second["gross_amount"]
    assert first["net_amount"] is not second["net_amount"]
    assert first["metadata"] is not second["metadata"]


def test_summary_rejects_count_total_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="must equal total entry count",
    ):
        summary(
            total_entry_count=10,
            successful_entry_count=9,
            failed_entry_count=0,
            excluded_entry_count=0,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "total_entry_count",
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
        "participant_count",
    ],
)
def test_summary_rejects_negative_counts(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        summary(**{field_name: -1})


@pytest.mark.parametrize(
    "field_name",
    [
        "total_entry_count",
        "successful_entry_count",
        "failed_entry_count",
        "excluded_entry_count",
        "participant_count",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [True, "1", 1.5, None],
)
def test_summary_rejects_invalid_count_types(
    field_name: str,
    invalid_value: object,
) -> None:
    with pytest.raises(TypeError):
        summary(**{field_name: invalid_value})


def test_summary_rejects_closed_before_opened() -> None:
    with pytest.raises(
        ValueError,
        match="must not precede opened_at",
    ):
        summary(
            closed_at=OPENED_AT - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "opened_at",
        "closed_at",
    ],
)
def test_summary_rejects_naive_timestamps(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        summary(
            **{
                field_name: COMPLETED_AT.replace(
                    tzinfo=None
                )
            }
        )


def test_summary_rejects_net_above_gross() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed gross amount",
    ):
        summary(
            gross_amount=money("100.00"),
            net_amount=money("100.01"),
        )


def test_summary_rejects_gross_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="gross amount currency",
    ):
        summary(
            gross_amount=money("1000.00", "USD"),
        )


def test_summary_rejects_net_currency_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="net amount currency",
    ):
        summary(
            net_amount=money("950.00", "USD"),
        )


def test_summary_rejects_empty_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        summary(settlement_currency_code="")


def test_summary_rejects_overlength_currency_code() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 3 characters",
    ):
        summary(settlement_currency_code="AUDD")


@pytest.mark.parametrize(
    "currency_code",
    ["AU", "12A"],
)
def test_summary_rejects_malformed_currency_code(
    currency_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="three-letter",
    ):
        summary(settlement_currency_code=currency_code)


def test_summary_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        summary(
            metadata={
                "authorization": "secret",
            }
        )


def test_module_all_contract_includes_section_6a() -> None:
    for symbol in (
        "SettlementFailure",
        "SettlementResult",
        "SettlementSummary",
    ):
        assert symbol in settlement_batch.__all__

    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )

    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )


def test_section_6a_domain_remains_internal() -> None:
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


def test_section_6a_has_no_execution_authority() -> None:
    for value_type in (
        SettlementFailure,
        SettlementResult,
        SettlementSummary,
    ):
        names = {
            name
            for name in dir(value_type)
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
        SettlementResult,
        SettlementSummary,
    ],
)
def test_section_6a_has_no_runtime_dependencies(
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
