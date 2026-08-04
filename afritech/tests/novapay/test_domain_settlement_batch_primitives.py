from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

import pytest

import afritech.novapay.domain.settlement_batch as settlement_batch
from afritech.novapay.domain.settlement_batch import (
    SettlementBatchId,
    SettlementBatchStatus,
    SettlementBatchType,
    SettlementEntryId,
    SettlementEntryStatus,
    SettlementInstructionId,
    SettlementMetadata,
    SettlementParticipant,
    SettlementParticipantId,
    SettlementParticipantType,
    SettlementReference,
    SettlementReferenceType,
    SettlementWindow,
)


UTC_OPEN = datetime(
    2026,
    8,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)

UTC_CLOSE = UTC_OPEN + timedelta(hours=4)
UTC_CUTOFF = UTC_OPEN + timedelta(hours=3)


IDENTIFIER_TYPES = (
    SettlementBatchId,
    SettlementEntryId,
    SettlementParticipantId,
    SettlementInstructionId,
)


@pytest.mark.parametrize(
    ("identifier_type", "raw", "expected"),
    [
        (
            SettlementBatchId,
            "settlement-batch-001",
            "settlement-batch-001",
        ),
        (
            SettlementEntryId,
            "entry:001",
            "entry:001",
        ),
        (
            SettlementParticipantId,
            "participant/001",
            "participant/001",
        ),
        (
            SettlementInstructionId,
            "instruction_001",
            "instruction_001",
        ),
    ],
)
def test_identifier_normalization(
    identifier_type: type,
    raw: str,
    expected: str,
) -> None:
    value = identifier_type.of(raw)

    assert value.value == expected
    assert str(value) == expected


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_preserves_instance(
    identifier_type: type,
) -> None:
    value = identifier_type.of("identifier-001")

    assert identifier_type.of(value) is value


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "invalid identifier?",
        "invalid#identifier",
        None,
        1,
        object(),
    ],
)
def test_identifier_rejects_invalid_values(
    identifier_type: type,
    raw: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        identifier_type.of(raw)


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_is_immutable(
    identifier_type: type,
) -> None:
    value = identifier_type.of("identifier-001")

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "identifier_type",
    IDENTIFIER_TYPES,
)
def test_identifier_is_orderable(
    identifier_type: type,
) -> None:
    first = identifier_type.of("identifier-001")
    second = identifier_type.of("identifier-002")

    assert first < second


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("draft", SettlementBatchStatus.DRAFT),
        ("open", SettlementBatchStatus.OPEN),
        ("validated", SettlementBatchStatus.VALIDATED),
        ("ready", SettlementBatchStatus.READY),
        ("processing", SettlementBatchStatus.PROCESSING),
        ("in progress", SettlementBatchStatus.PROCESSING),
        ("complete", SettlementBatchStatus.COMPLETE),
        ("completed", SettlementBatchStatus.COMPLETE),
        (
            "partially complete",
            SettlementBatchStatus.PARTIALLY_COMPLETE,
        ),
        ("failed", SettlementBatchStatus.FAILURE),
        ("cancelled", SettlementBatchStatus.CANCELED),
        ("expired", SettlementBatchStatus.EXPIRED),
        ("reconciled", SettlementBatchStatus.RECONCILED),
    ],
)
def test_batch_status_parsing(
    raw: object,
    expected: SettlementBatchStatus,
) -> None:
    assert SettlementBatchStatus.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "gross settlement",
            SettlementBatchType.GROSS_SETTLEMENT,
        ),
        ("gross", SettlementBatchType.GROSS_SETTLEMENT),
        ("netting", SettlementBatchType.NETTING),
        ("net", SettlementBatchType.NETTING),
        ("daily", SettlementBatchType.DAILY),
        ("daily batch", SettlementBatchType.DAILY),
        ("intraday", SettlementBatchType.INTRADAY),
        (
            "intraday batch",
            SettlementBatchType.INTRADAY,
        ),
        ("manual", SettlementBatchType.MANUAL),
        ("manual batch", SettlementBatchType.MANUAL),
        ("automatic", SettlementBatchType.AUTOMATIC),
        (
            "automatic batch",
            SettlementBatchType.AUTOMATIC,
        ),
        ("provider", SettlementBatchType.PROVIDER),
        ("corridor", SettlementBatchType.CORRIDOR),
        ("currency", SettlementBatchType.CURRENCY),
        ("merchant", SettlementBatchType.MERCHANT),
    ],
)
def test_batch_type_parsing(
    raw: object,
    expected: SettlementBatchType,
) -> None:
    assert SettlementBatchType.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pending", SettlementEntryStatus.PENDING),
        ("validated", SettlementEntryStatus.VALIDATED),
        ("included", SettlementEntryStatus.INCLUDED),
        ("processing", SettlementEntryStatus.PROCESSING),
        ("in progress", SettlementEntryStatus.PROCESSING),
        ("complete", SettlementEntryStatus.COMPLETE),
        ("completed", SettlementEntryStatus.COMPLETE),
        ("failed", SettlementEntryStatus.FAILURE),
        ("excluded", SettlementEntryStatus.EXCLUDED),
        ("reversed", SettlementEntryStatus.REVERSED),
    ],
)
def test_entry_status_parsing(
    raw: object,
    expected: SettlementEntryStatus,
) -> None:
    assert SettlementEntryStatus.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("wallet", SettlementParticipantType.WALLET),
        ("customer", SettlementParticipantType.CUSTOMER),
        (
            "financial account",
            SettlementParticipantType.FINANCIAL_ACCOUNT,
        ),
        ("provider", SettlementParticipantType.PROVIDER),
        ("merchant", SettlementParticipantType.MERCHANT),
        ("agent", SettlementParticipantType.AGENT),
        ("treasury", SettlementParticipantType.TREASURY),
        (
            "clearing account",
            SettlementParticipantType.CLEARING_ACCOUNT,
        ),
        (
            "settlement account",
            SettlementParticipantType.SETTLEMENT_ACCOUNT,
        ),
        (
            "external system",
            SettlementParticipantType.EXTERNAL_SYSTEM,
        ),
    ],
)
def test_participant_type_parsing(
    raw: object,
    expected: SettlementParticipantType,
) -> None:
    assert SettlementParticipantType.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("transaction", SettlementReferenceType.TRANSACTION),
        ("transfer", SettlementReferenceType.TRANSFER),
        ("remittance", SettlementReferenceType.REMITTANCE),
        (
            "journal entry",
            SettlementReferenceType.JOURNAL_ENTRY,
        ),
        (
            "ledger account",
            SettlementReferenceType.LEDGER_ACCOUNT,
        ),
        (
            "provider batch",
            SettlementReferenceType.PROVIDER_BATCH,
        ),
        (
            "reconciliation",
            SettlementReferenceType.RECONCILIATION,
        ),
        ("external", SettlementReferenceType.EXTERNAL),
    ],
)
def test_reference_type_parsing(
    raw: object,
    expected: SettlementReferenceType,
) -> None:
    assert SettlementReferenceType.parse(raw) is expected


@pytest.mark.parametrize(
    "enum_type",
    [
        SettlementBatchStatus,
        SettlementBatchType,
        SettlementEntryStatus,
        SettlementParticipantType,
        SettlementReferenceType,
    ],
)
@pytest.mark.parametrize(
    "raw",
    [
        "",
        "unsupported",
        None,
        1,
        object(),
    ],
)
def test_enums_reject_invalid_values(
    enum_type: type,
    raw: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        enum_type.parse(raw)


def test_reference_construction() -> None:
    value = SettlementReference.create(
        reference_type="remittance",
        reference_id="remittance-001",
        external_reference="provider-reference-001",
    )

    assert (
        value.reference_type
        is SettlementReferenceType.REMITTANCE
    )
    assert value.reference_id == "remittance-001"
    assert (
        value.external_reference
        == "provider-reference-001"
    )


def test_reference_without_external_reference() -> None:
    value = SettlementReference.create(
        reference_type="transfer",
        reference_id="transfer-001",
    )

    assert value.external_reference is None


def test_reference_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementReference)
    } == {
        "reference_type",
        "reference_id",
        "external_reference",
    }


def test_reference_is_immutable() -> None:
    value = SettlementReference.create(
        reference_type="transaction",
        reference_id="transaction-001",
    )

    with pytest.raises(FrozenInstanceError):
        value.reference_id = "changed"  # type: ignore[misc]


def test_reference_canonical_dict() -> None:
    value = SettlementReference.create(
        reference_type="remittance",
        reference_id="remittance-001",
        external_reference="external-001",
    )

    assert value.canonical_dict() == {
        "reference_type": "remittance",
        "reference_id": "remittance-001",
        "external_reference": "external-001",
    }


def test_reference_canonical_dict_is_fresh() -> None:
    value = SettlementReference.create(
        reference_type="transfer",
        reference_id="transfer-001",
    )

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("reference_id", ""),
        ("reference_id", "invalid?"),
        ("external_reference", ""),
        ("external_reference", "invalid?"),
    ],
)
def test_reference_rejects_invalid_identifiers(
    field_name: str,
    field_value: object,
) -> None:
    kwargs: dict[str, object] = {
        "reference_type": "transfer",
        "reference_id": "transfer-001",
        "external_reference": "external-001",
        field_name: field_value,
    }

    with pytest.raises((TypeError, ValueError)):
        SettlementReference.create(**kwargs)


def test_participant_construction() -> None:
    value = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="settlement account",
        account_reference="account-001",
        currency_code="aud",
        jurisdiction_code="au",
        provider_code="Provider One",
    )

    assert value.participant_id == (
        SettlementParticipantId.of("participant-001")
    )
    assert (
        value.participant_type
        is SettlementParticipantType.SETTLEMENT_ACCOUNT
    )
    assert value.account_reference == "account-001"
    assert value.currency_code == "AUD"
    assert value.jurisdiction_code == "AU"
    assert value.provider_code == "provider_one"


def test_participant_optional_fields() -> None:
    value = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="wallet",
        account_reference="wallet-001",
        currency_code="usd",
    )

    assert value.jurisdiction_code is None
    assert value.provider_code is None


def test_participant_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementParticipant)
    } == {
        "participant_id",
        "participant_type",
        "account_reference",
        "currency_code",
        "jurisdiction_code",
        "provider_code",
    }


def test_participant_is_immutable() -> None:
    value = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="wallet",
        account_reference="wallet-001",
        currency_code="AUD",
    )

    with pytest.raises(FrozenInstanceError):
        value.currency_code = "USD"  # type: ignore[misc]


def test_participant_canonical_dict() -> None:
    value = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="provider",
        account_reference="provider-account-001",
        currency_code="eur",
        jurisdiction_code="deu",
        provider_code="Provider EU",
    )

    assert value.canonical_dict() == {
        "participant_id": "participant-001",
        "participant_type": "provider",
        "account_reference": "provider-account-001",
        "currency_code": "EUR",
        "jurisdiction_code": "DEU",
        "provider_code": "provider_eu",
    }


def test_participant_canonical_dict_is_fresh() -> None:
    value = SettlementParticipant.create(
        participant_id="participant-001",
        participant_type="wallet",
        account_reference="wallet-001",
        currency_code="AUD",
    )

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second


@pytest.mark.parametrize(
    "currency_code",
    [
        "",
        "AU",
        "AUDD",
        "12A",
        None,
    ],
)
def test_participant_rejects_invalid_currency(
    currency_code: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        SettlementParticipant.create(
            participant_id="participant-001",
            participant_type="wallet",
            account_reference="wallet-001",
            currency_code=currency_code,
        )


@pytest.mark.parametrize(
    "jurisdiction_code",
    [
        "",
        "A",
        "AUS1",
        "12",
    ],
)
def test_participant_rejects_invalid_jurisdiction(
    jurisdiction_code: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        SettlementParticipant.create(
            participant_id="participant-001",
            participant_type="wallet",
            account_reference="wallet-001",
            currency_code="AUD",
            jurisdiction_code=jurisdiction_code,
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("participant_id", ""),
        ("participant_id", "invalid?"),
        ("account_reference", ""),
        ("account_reference", "invalid?"),
    ],
)
def test_participant_rejects_invalid_identifiers(
    field_name: str,
    field_value: object,
) -> None:
    kwargs: dict[str, object] = {
        "participant_id": "participant-001",
        "participant_type": "wallet",
        "account_reference": "wallet-001",
        "currency_code": "AUD",
        field_name: field_value,
    }

    with pytest.raises((TypeError, ValueError)):
        SettlementParticipant.create(**kwargs)


def test_window_construction() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
        cutoff_at=UTC_CUTOFF,
        timezone_name="Australia/Melbourne",
    )

    assert value.opens_at == UTC_OPEN
    assert value.closes_at == UTC_CLOSE
    assert value.cutoff_at == UTC_CUTOFF
    assert value.timezone_name == "Australia/Melbourne"
    assert value.duration_seconds == 14400


def test_window_without_cutoff() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
    )

    assert value.cutoff_at is None
    assert value.timezone_name == "UTC"


@pytest.mark.parametrize(
    "timestamp",
    [
        UTC_OPEN,
        UTC_CUTOFF,
        UTC_CLOSE,
    ],
)
def test_window_contains_boundary_timestamps(
    timestamp: datetime,
) -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
        cutoff_at=UTC_CUTOFF,
    )

    assert value.contains(timestamp) is True


@pytest.mark.parametrize(
    "timestamp",
    [
        UTC_OPEN - timedelta(microseconds=1),
        UTC_CLOSE + timedelta(microseconds=1),
    ],
)
def test_window_excludes_outside_timestamps(
    timestamp: datetime,
) -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
    )

    assert value.contains(timestamp) is False


def test_window_normalizes_timezone_to_utc() -> None:
    offset_timezone = timezone(timedelta(hours=10))

    opens_at = datetime(
        2026,
        8,
        4,
        10,
        0,
        tzinfo=offset_timezone,
    )

    closes_at = datetime(
        2026,
        8,
        4,
        14,
        0,
        tzinfo=offset_timezone,
    )

    value = SettlementWindow(
        opens_at=opens_at,
        closes_at=closes_at,
    )

    assert value.opens_at == UTC_OPEN
    assert value.closes_at == UTC_CLOSE


def test_window_is_immutable() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
    )

    with pytest.raises(FrozenInstanceError):
        value.closes_at = UTC_OPEN  # type: ignore[misc]


def test_window_field_contract() -> None:
    assert {
        item.name
        for item in fields(SettlementWindow)
    } == {
        "opens_at",
        "closes_at",
        "cutoff_at",
        "timezone_name",
    }


def test_window_canonical_dict() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
        cutoff_at=UTC_CUTOFF,
        timezone_name="Australia/Melbourne",
    )

    assert value.canonical_dict() == {
        "opens_at": UTC_OPEN.isoformat(),
        "closes_at": UTC_CLOSE.isoformat(),
        "cutoff_at": UTC_CUTOFF.isoformat(),
        "timezone_name": "Australia/Melbourne",
        "duration_seconds": 14400,
    }


def test_window_canonical_dict_is_fresh() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
    )

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second


@pytest.mark.parametrize(
    ("opens_at", "closes_at"),
    [
        (UTC_OPEN, UTC_OPEN),
        (UTC_CLOSE, UTC_OPEN),
    ],
)
def test_window_rejects_invalid_chronology(
    opens_at: datetime,
    closes_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="after opens_at",
    ):
        SettlementWindow(
            opens_at=opens_at,
            closes_at=closes_at,
        )


@pytest.mark.parametrize(
    ("opens_at", "closes_at"),
    [
        (
            UTC_OPEN.replace(tzinfo=None),
            UTC_CLOSE,
        ),
        (
            UTC_OPEN,
            UTC_CLOSE.replace(tzinfo=None),
        ),
    ],
)
def test_window_rejects_naive_datetimes(
    opens_at: datetime,
    closes_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        SettlementWindow(
            opens_at=opens_at,
            closes_at=closes_at,
        )


@pytest.mark.parametrize(
    "cutoff_at",
    [
        UTC_OPEN - timedelta(seconds=1),
        UTC_CLOSE + timedelta(seconds=1),
    ],
)
def test_window_rejects_cutoff_outside_window(
    cutoff_at: datetime,
) -> None:
    with pytest.raises(
        ValueError,
        match="within the settlement window",
    ):
        SettlementWindow(
            opens_at=UTC_OPEN,
            closes_at=UTC_CLOSE,
            cutoff_at=cutoff_at,
        )


def test_window_contains_rejects_naive_datetime() -> None:
    value = SettlementWindow(
        opens_at=UTC_OPEN,
        closes_at=UTC_CLOSE,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        value.contains(
            UTC_OPEN.replace(tzinfo=None)
        )


def test_metadata_defaults_empty() -> None:
    value = SettlementMetadata.of()

    assert value.values == {}
    assert isinstance(
        value.values,
        MappingProxyType,
    )


def test_metadata_preserves_instance() -> None:
    value = SettlementMetadata.of(
        {"version": "v1"}
    )

    assert SettlementMetadata.of(value) is value


def test_metadata_normalization() -> None:
    value = SettlementMetadata.of(
        {
            "Settlement Version": "v1",
            "Source-System": "novapay",
            "Attempt": 1,
            "Automatic": True,
            "Tags": ["daily", "aud"],
            "Nested": {
                "Batch Reference": "batch-001",
            },
            "Observed At": UTC_OPEN,
        }
    )

    assert value.values == {
        "attempt": 1,
        "automatic": True,
        "nested": {
            "batch_reference": "batch-001",
        },
        "observed_at": UTC_OPEN.isoformat(),
        "settlement_version": "v1",
        "source_system": "novapay",
        "tags": (
            "daily",
            "aud",
        ),
    }

    assert isinstance(
        value.values,
        MappingProxyType,
    )

    assert isinstance(
        value.values["nested"],
        MappingProxyType,
    )


def test_metadata_is_immutable() -> None:
    value = SettlementMetadata.of(
        {"version": "v1"}
    )

    with pytest.raises(FrozenInstanceError):
        value.values = {}  # type: ignore[misc]

    with pytest.raises(TypeError):
        value.values["version"] = "v2"  # type: ignore[index]


def test_nested_metadata_is_immutable() -> None:
    value = SettlementMetadata.of(
        {
            "nested": {
                "version": "v1",
            }
        }
    )

    nested = value.values["nested"]

    assert isinstance(nested, MappingProxyType)

    with pytest.raises(TypeError):
        nested["version"] = "v2"  # type: ignore[index]


def test_metadata_canonical_dict() -> None:
    value = SettlementMetadata.of(
        {
            "version": "v1",
            "attempt": 1,
        }
    )

    assert value.canonical_dict() == {
        "attempt": 1,
        "version": "v1",
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
        "secret_value",
    ],
)
def test_metadata_rejects_sensitive_keys(
    sensitive_key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        SettlementMetadata.of(
            {sensitive_key: "sensitive"}
        )


@pytest.mark.parametrize(
    "invalid_key",
    [
        "",
        "1invalid",
        "_invalid",
        "invalid?",
        None,
        1,
    ],
)
def test_metadata_rejects_invalid_keys(
    invalid_key: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        SettlementMetadata.of(
            {invalid_key: "value"}
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        object(),
        {1, 2},
        complex(1, 2),
    ],
)
def test_metadata_rejects_unsupported_values(
    invalid_value: object,
) -> None:
    with pytest.raises(TypeError):
        SettlementMetadata.of(
            {"value": invalid_value}
        )


@pytest.mark.parametrize(
    "invalid_float",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_metadata_rejects_non_finite_floats(
    invalid_float: float,
) -> None:
    with pytest.raises(ValueError):
        SettlementMetadata.of(
            {"value": invalid_float}
        )


def test_metadata_rejects_empty_string_value() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        SettlementMetadata.of(
            {"value": ""}
        )


def test_module_all_contract() -> None:
    assert settlement_batch.__all__ == [
        "SettlementBatch",
        "SettlementBatchId",
        "SettlementBatchStatus",
        "SettlementBatchType",
        "SettlementEntry",
        "SettlementEntryId",
        "SettlementEntryStatus",
        "SettlementFailure",
        "SettlementInstruction",
        "SettlementInstructionId",
        "SettlementInstructionMetadata",
        "SettlementMetadata",
        "SettlementParticipant",
        "SettlementParticipantId",
        "SettlementParticipantType",
        "SettlementReference",
        "SettlementReferenceType",
        "SettlementResult",
        "SettlementSummary",
        "SettlementWindow",
    ]

    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )

    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )


def test_primitives_remain_internal() -> None:
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


def test_primitives_have_no_operational_authority() -> None:
    value_types = (
        SettlementReference,
        SettlementParticipant,
        SettlementWindow,
        SettlementMetadata,
    )

    for value_type in value_types:
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


def test_participant_has_no_runtime_dependencies() -> None:
    field_names = {
        item.name
        for item in fields(SettlementParticipant)
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
