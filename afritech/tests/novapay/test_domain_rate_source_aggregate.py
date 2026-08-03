from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.exchange_rate_provider import (
    ExchangeRateProviderId,
    ProviderTrustLevel,
    RateSource,
    RateSourceId,
    RateSourceMetadata,
    RateSourceStatus,
    RateSourceType,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    0,
    0,
    tzinfo=timezone.utc,
)


def rate_source(
    **overrides: object,
) -> RateSource:
    values: dict[str, object] = {
        "rate_source_id": "source-rba-reference",
        "provider_id": "provider-rba",
        "source_type": "central_bank_reference",
        "status": "active",
        "trust_level": "authoritative",
        "priority": 10,
        "supported_currency_pairs": (
            "AUD/USD",
            "AUD/NZD",
        ),
        "maximum_staleness_seconds": 3600,
        "expected_latency_ms": 500,
        "expected_reliability": Decimal("0.999"),
        "metadata": {
            "jurisdiction": "AU",
            "publication": "reference-rate",
        },
        "created_at": CREATED_AT,
    }

    values.update(overrides)

    return RateSource.create(
        **values,  # type: ignore[arg-type]
    )


def test_create_rate_source() -> None:
    value = rate_source()

    assert value.rate_source_id == RateSourceId(
        "source-rba-reference"
    )
    assert value.provider_id == ExchangeRateProviderId(
        "provider-rba"
    )
    assert value.source_type is (
        RateSourceType.CENTRAL_BANK_REFERENCE
    )
    assert value.status is RateSourceStatus.ACTIVE
    assert value.trust_level is (
        ProviderTrustLevel.AUTHORITATIVE
    )
    assert value.priority == 10
    assert value.version == 1
    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_rate_source_is_immutable() -> None:
    value = rate_source()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_rate_source_uses_slots() -> None:
    assert not hasattr(rate_source(), "__dict__")


def test_rate_source_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(RateSource)
    } == {
        "rate_source_id",
        "provider_id",
        "source_type",
        "status",
        "trust_level",
        "priority",
        "supported_currency_pairs",
        "maximum_staleness_seconds",
        "expected_latency_ms",
        "expected_reliability",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_rate_source_factory_normalizes_values() -> None:
    value = rate_source(
        rate_source_id=" source-rba-reference ",
        provider_id=" provider-rba ",
        source_type=" central-bank-reference ",
        status=" ACTIVE ",
        trust_level=" authoritative ",
        supported_currency_pairs=(
            "aud/usd",
            "AUD/NZD",
        ),
    )

    assert value.rate_source_id.value == (
        "source-rba-reference"
    )
    assert value.provider_id.value == "provider-rba"
    assert value.source_type is (
        RateSourceType.CENTRAL_BANK_REFERENCE
    )
    assert value.status is RateSourceStatus.ACTIVE
    assert value.trust_level is (
        ProviderTrustLevel.AUTHORITATIVE
    )
    assert value.supported_currency_pairs == (
        "AUD/NZD",
        "AUD/USD",
    )


def test_rate_source_provider_linkage() -> None:
    value = rate_source(
        provider_id="provider-central-bank-au"
    )

    assert value.provider_id == ExchangeRateProviderId(
        "provider-central-bank-au"
    )
    assert value.provider_reference == (
        "provider-central-bank-au"
    )


def test_rate_source_reference_uses_identifier() -> None:
    value = rate_source(
        rate_source_id="source-reference-001"
    )

    assert value.source_reference == (
        "source-reference-001"
    )


def test_rate_source_references_are_strings() -> None:
    value = rate_source()

    assert isinstance(value.source_reference, str)
    assert isinstance(value.provider_reference, str)
    assert value.source_reference == (
        value.rate_source_id.value
    )
    assert value.provider_reference == (
        value.provider_id.value
    )


def test_rate_source_priority_zero_is_allowed() -> None:
    value = rate_source(priority=0)

    assert value.priority == 0


def test_rate_source_priority_is_preserved() -> None:
    value = rate_source(priority=250)

    assert value.priority == 250


def test_rate_source_rejects_negative_priority() -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to 0",
    ):
        rate_source(priority=-1)


@pytest.mark.parametrize(
    "priority",
    [
        True,
        "10",
        Decimal("10"),
    ],
)
def test_rate_source_rejects_non_integer_priority(
    priority: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        rate_source(priority=priority)


def test_rate_source_supported_pairs_are_sorted() -> None:
    value = rate_source(
        supported_currency_pairs=(
            "USD/EUR",
            "AUD/USD",
            "AUD/NZD",
        )
    )

    assert value.supported_currency_pairs == (
        "AUD/NZD",
        "AUD/USD",
        "USD/EUR",
    )


def test_rate_source_supports_pair() -> None:
    value = rate_source()

    assert value.supports_pair("aud/usd") is True
    assert value.supports_pair("AUD/NZD") is True
    assert value.supports_pair("AUD/EUR") is False


@pytest.mark.parametrize(
    "pair",
    [
        "AUDUSD",
        "AUD/",
        "/USD",
        "AU/USD",
        "AUD/USDD",
        "123/USD",
    ],
)
def test_rate_source_rejects_invalid_pair(
    pair: str,
) -> None:
    with pytest.raises(ValueError):
        rate_source(
            supported_currency_pairs=(pair,)
        )


def test_rate_source_rejects_duplicate_pairs() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        rate_source(
            supported_currency_pairs=(
                "AUD/USD",
                "AUD/USD",
            )
        )


def test_rate_source_freshness_contract() -> None:
    value = rate_source(
        maximum_staleness_seconds=120,
    )

    assert value.maximum_staleness_seconds == 120


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_rate_source_rejects_invalid_staleness(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        rate_source(
            maximum_staleness_seconds=value
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "300",
        Decimal("300"),
    ],
)
def test_rate_source_rejects_non_integer_staleness(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        rate_source(
            maximum_staleness_seconds=value
        )


def test_rate_source_latency_is_optional() -> None:
    value = rate_source(
        expected_latency_ms=None
    )

    assert value.expected_latency_ms is None


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_rate_source_rejects_invalid_latency(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        rate_source(
            expected_latency_ms=value
        )


def test_rate_source_reliability_is_optional() -> None:
    value = rate_source(
        expected_reliability=None
    )

    assert value.expected_reliability is None


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0"),
        Decimal("0.50"),
        Decimal("1"),
    ],
)
def test_rate_source_accepts_valid_reliability(
    value: Decimal,
) -> None:
    source = rate_source(
        expected_reliability=value
    )

    assert source.expected_reliability == value


@pytest.mark.parametrize(
    "value",
    [
        Decimal("-0.01"),
        Decimal("1.01"),
    ],
)
def test_rate_source_rejects_invalid_reliability(
    value: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        rate_source(
            expected_reliability=value
        )


def test_rate_source_rejects_float_reliability() -> None:
    with pytest.raises(
        TypeError,
        match="must not be constructed from float",
    ):
        rate_source(
            expected_reliability=0.99
        )


def test_rate_source_metadata_contract() -> None:
    value = rate_source()

    assert value.metadata == RateSourceMetadata(
        {
            "jurisdiction": "AU",
            "publication": "reference-rate",
        }
    )


def test_rate_source_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        rate_source(
            metadata={
                "api_key": "secret",
            }
        )


def test_active_rate_source_properties() -> None:
    value = rate_source(status="active")

    assert value.is_active is True
    assert value.is_terminal is False


def test_retired_rate_source_properties() -> None:
    value = rate_source(status="retired")

    assert value.is_active is False
    assert value.is_terminal is True


@pytest.mark.parametrize(
    "status",
    [
        "draft",
        "degraded",
        "suspended",
    ],
)
def test_non_active_non_terminal_rate_source(
    status: str,
) -> None:
    value = rate_source(status=status)

    assert value.is_active is False
    assert value.is_terminal is False


def test_rate_source_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        rate_source(
            created_at=datetime(
                2026,
                8,
                3,
                0,
                0,
            )
        )


def test_rate_source_normalizes_created_at_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))

    source_time = datetime(
        2026,
        8,
        3,
        10,
        0,
        tzinfo=plus_ten,
    )

    value = rate_source(created_at=source_time)

    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_direct_constructor_rejects_naive_updated_at() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        RateSource(
            rate_source_id=value.rate_source_id,
            provider_id=value.provider_id,
            source_type=value.source_type,
            status=value.status,
            trust_level=value.trust_level,
            priority=value.priority,
            supported_currency_pairs=(
                value.supported_currency_pairs
            ),
            maximum_staleness_seconds=(
                value.maximum_staleness_seconds
            ),
            expected_latency_ms=(
                value.expected_latency_ms
            ),
            expected_reliability=(
                value.expected_reliability
            ),
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=datetime(
                2026,
                8,
                3,
                0,
                1,
            ),
            version=1,
        )


def test_updated_at_must_not_precede_created_at() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        RateSource(
            rate_source_id=value.rate_source_id,
            provider_id=value.provider_id,
            source_type=value.source_type,
            status=value.status,
            trust_level=value.trust_level,
            priority=value.priority,
            supported_currency_pairs=(
                value.supported_currency_pairs
            ),
            maximum_staleness_seconds=(
                value.maximum_staleness_seconds
            ),
            expected_latency_ms=(
                value.expected_latency_ms
            ),
            expected_reliability=(
                value.expected_reliability
            ),
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=(
                value.created_at
                - timedelta(seconds=1)
            ),
            version=1,
        )


@pytest.mark.parametrize(
    "version",
    [
        0,
        -1,
    ],
)
def test_rate_source_rejects_invalid_version(
    version: int,
) -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        RateSource(
            rate_source_id=value.rate_source_id,
            provider_id=value.provider_id,
            source_type=value.source_type,
            status=value.status,
            trust_level=value.trust_level,
            priority=value.priority,
            supported_currency_pairs=(
                value.supported_currency_pairs
            ),
            maximum_staleness_seconds=(
                value.maximum_staleness_seconds
            ),
            expected_latency_ms=(
                value.expected_latency_ms
            ),
            expected_reliability=(
                value.expected_reliability
            ),
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=version,
        )


@pytest.mark.parametrize(
    "version",
    [
        True,
        "1",
        Decimal("1"),
    ],
)
def test_rate_source_rejects_non_integer_version(
    version: object,
) -> None:
    value = rate_source()

    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        RateSource(
            rate_source_id=value.rate_source_id,
            provider_id=value.provider_id,
            source_type=value.source_type,
            status=value.status,
            trust_level=value.trust_level,
            priority=value.priority,
            supported_currency_pairs=(
                value.supported_currency_pairs
            ),
            maximum_staleness_seconds=(
                value.maximum_staleness_seconds
            ),
            expected_latency_ms=(
                value.expected_latency_ms
            ),
            expected_reliability=(
                value.expected_reliability
            ),
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=version,  # type: ignore[arg-type]
        )


def test_rate_source_canonical_dict() -> None:
    payload = rate_source().canonical_dict()

    assert list(payload) == [
        "rate_source_id",
        "provider_id",
        "source_type",
        "status",
        "trust_level",
        "priority",
        "supported_currency_pairs",
        "maximum_staleness_seconds",
        "expected_latency_ms",
        "expected_reliability",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["rate_source_id"] == (
        "source-rba-reference"
    )
    assert payload["provider_id"] == "provider-rba"
    assert payload["source_type"] == (
        "central_bank_reference"
    )
    assert payload["status"] == "active"
    assert payload["trust_level"] == (
        "authoritative"
    )
    assert payload["priority"] == 10
    assert payload["supported_currency_pairs"] == [
        "AUD/NZD",
        "AUD/USD",
    ]
    assert payload["maximum_staleness_seconds"] == 3600
    assert payload["expected_latency_ms"] == 500
    assert payload["expected_reliability"] == "0.999"
    assert payload["metadata"] == {
        "jurisdiction": "AU",
        "publication": "reference-rate",
    }
    assert payload["created_at"] == (
        "2026-08-03T00:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-03T00:00:00+00:00"
    )
    assert payload["version"] == 1


def test_rate_source_canonical_dict_is_fresh() -> None:
    value = rate_source()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["supported_currency_pairs"]
        is not second["supported_currency_pairs"]
    )
    assert first["metadata"] is not second["metadata"]


def test_rate_source_preserves_value_objects() -> None:
    source_id = RateSourceId(
        "source-rba-reference"
    )
    provider_id = ExchangeRateProviderId(
        "provider-rba"
    )
    metadata = RateSourceMetadata(
        {
            "jurisdiction": "AU",
        }
    )

    value = RateSource(
        rate_source_id=source_id,
        provider_id=provider_id,
        source_type=(
            RateSourceType.CENTRAL_BANK_REFERENCE
        ),
        status=RateSourceStatus.ACTIVE,
        trust_level=(
            ProviderTrustLevel.AUTHORITATIVE
        ),
        priority=10,
        supported_currency_pairs=("AUD/USD",),
        maximum_staleness_seconds=3600,
        expected_latency_ms=500,
        expected_reliability=Decimal("0.999"),
        metadata=metadata,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        version=1,
    )

    assert value.rate_source_id is source_id
    assert value.provider_id is provider_id
    assert value.metadata is metadata


def test_rate_source_contains_no_provider_aggregate() -> None:
    value = rate_source()

    assert not hasattr(value, "provider")
    assert not hasattr(value, "exchange_rate_provider")


def test_rate_source_contains_no_rate_values() -> None:
    value = rate_source()

    for forbidden in (
        "rate",
        "spread",
        "bid",
        "ask",
        "mid",
        "exchange_rate",
        "fx_quote",
    ):
        assert not hasattr(value, forbidden)


def test_rate_source_contains_no_runtime_authority() -> None:
    value = rate_source()

    for forbidden in (
        "request",
        "fetch",
        "connect",
        "stream",
        "publish_rate",
        "calculate_rate",
        "select_rate",
        "lock_rate",
        "convert",
        "post",
        "settle",
        "save",
        "repository",
        "database",
        "provider_client",
        "http_client",
        "api_key",
        "credentials",
    ):
        assert not hasattr(value, forbidden)


def test_provider_module_contract() -> None:
    from afritech.novapay.domain import (
        exchange_rate_provider,
    )

    assert exchange_rate_provider.__all__ == [
        "ExchangeRateProvider",
        "ExchangeRateProviderId",
        "ExchangeRateProviderRegistry",
        "ExchangeRateProviderRegistryId",
        "ExchangeRateProviderStatus",
        "ExchangeRateProviderType",
        "ProviderCapabilities",
        "ProviderEndpoint",
        "ProviderMetadata",
        "ProviderName",
        "ProviderTrustLevel",
        "RateSource",
        "RateSourceId",
        "RateSourceMetadata",
        "RateSourceStatus",
        "RateSourceType",
    ]


def test_registry_is_available_in_module() -> None:
    from afritech.novapay.domain import (
        exchange_rate_provider,
    )

    assert hasattr(
        exchange_rate_provider,
        "ExchangeRateProviderRegistry",
    )
