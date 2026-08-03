from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.exchange_rate_provider import (
    ExchangeRateProvider,
    ExchangeRateProviderId,
    ExchangeRateProviderStatus,
    ExchangeRateProviderType,
    ProviderCapabilities,
    ProviderEndpoint,
    ProviderMetadata,
    ProviderName,
    ProviderTrustLevel,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    9,
    0,
    tzinfo=timezone.utc,
)


def provider(
    **overrides: object,
) -> ExchangeRateProvider:
    values: dict[str, object] = {
        "provider_id": "provider-rba",
        "name": "Reserve Bank of Australia",
        "provider_type": "central_bank",
        "status": "active",
        "trust_level": "authoritative",
        "capabilities": {
            "supported_currency_pairs": (
                "AUD/USD",
                "AUD/NZD",
            ),
            "supported_rate_source_types": (
                "central_bank_reference",
                "mid_market",
            ),
            "supports_historical_rates": True,
            "supports_inverse_rates": True,
            "maximum_staleness_seconds": 3600,
            "expected_latency_ms": 500,
            "expected_reliability": Decimal("0.999"),
        },
        "endpoint": (
            "https://rates.example.com/v1/reference"
        ),
        "endpoint_description": (
            "Public reference-rate feed"
        ),
        "metadata": {
            "jurisdiction": "AU",
            "data_region": "Australia",
            "audited": True,
        },
        "created_at": CREATED_AT,
    }

    values.update(overrides)

    return ExchangeRateProvider.create(
        **values,  # type: ignore[arg-type]
    )


def test_create_exchange_rate_provider() -> None:
    value = provider()

    assert value.provider_id == ExchangeRateProviderId(
        "provider-rba"
    )
    assert value.name == ProviderName(
        "Reserve Bank of Australia"
    )
    assert value.provider_type is (
        ExchangeRateProviderType.CENTRAL_BANK
    )
    assert value.status is (
        ExchangeRateProviderStatus.ACTIVE
    )
    assert value.trust_level is (
        ProviderTrustLevel.AUTHORITATIVE
    )
    assert value.version == 1
    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_provider_is_immutable() -> None:
    value = provider()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_provider_uses_slots() -> None:
    assert not hasattr(provider(), "__dict__")


def test_provider_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(ExchangeRateProvider)
    } == {
        "provider_id",
        "name",
        "provider_type",
        "status",
        "trust_level",
        "capabilities",
        "endpoint",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_provider_factory_normalizes_values() -> None:
    value = provider(
        provider_id=" provider-rba ",
        name=" Reserve   Bank of Australia ",
        provider_type=" central-bank ",
        status=" ACTIVE ",
        trust_level=" authoritative ",
    )

    assert value.provider_id.value == "provider-rba"
    assert value.name.value == (
        "Reserve Bank of Australia"
    )
    assert value.provider_type is (
        ExchangeRateProviderType.CENTRAL_BANK
    )
    assert value.status is (
        ExchangeRateProviderStatus.ACTIVE
    )
    assert value.trust_level is (
        ProviderTrustLevel.AUTHORITATIVE
    )


def test_provider_endpoint_contract() -> None:
    value = provider()

    assert value.endpoint == ProviderEndpoint.of(
        "https://rates.example.com/v1/reference",
        description="Public reference-rate feed",
    )
    assert value.endpoint is not None
    assert value.endpoint.hostname == (
        "rates.example.com"
    )


def test_provider_endpoint_is_optional() -> None:
    value = provider(
        endpoint=None,
        endpoint_description=None,
    )

    assert value.endpoint is None


def test_provider_capabilities_contract() -> None:
    value = provider()

    assert value.capabilities == ProviderCapabilities(
        supported_currency_pairs=(
            "AUD/NZD",
            "AUD/USD",
        ),
        supported_rate_source_types=(
            "central_bank_reference",
            "mid_market",
        ),
        supports_historical_rates=True,
        supports_inverse_rates=True,
        maximum_staleness_seconds=3600,
        expected_latency_ms=500,
        expected_reliability=Decimal("0.999"),
    )


def test_provider_metadata_contract() -> None:
    value = provider()

    assert value.metadata == ProviderMetadata(
        {
            "jurisdiction": "AU",
            "data_region": "Australia",
            "audited": True,
        }
    )


def test_provider_supports_pair() -> None:
    value = provider()

    assert value.supports_pair("aud/usd") is True
    assert value.supports_pair("AUD/EUR") is False


def test_provider_supports_source_type() -> None:
    value = provider()

    assert value.supports_source_type(
        "central_bank_reference"
    ) is True
    assert value.supports_source_type(
        "spot"
    ) is False


def test_active_provider_properties() -> None:
    value = provider(status="active")

    assert value.is_active is True
    assert value.is_terminal is False


def test_retired_provider_properties() -> None:
    value = provider(status="retired")

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
def test_non_active_non_terminal_provider(
    status: str,
) -> None:
    value = provider(status=status)

    assert value.is_active is False
    assert value.is_terminal is False


def test_provider_reference_uses_identifier() -> None:
    value = provider(
        provider_id="provider-reference-001"
    )

    assert value.provider_reference == (
        "provider-reference-001"
    )


def test_provider_reference_remains_string_compatible() -> None:
    value = provider()

    assert isinstance(value.provider_reference, str)
    assert value.provider_reference == (
        value.provider_id.value
    )


def test_provider_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        provider(
            created_at=datetime(
                2026,
                8,
                3,
                9,
                0,
            )
        )


def test_provider_normalizes_created_at_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))

    source_time = datetime(
        2026,
        8,
        3,
        19,
        0,
        tzinfo=plus_ten,
    )

    value = provider(created_at=source_time)

    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT


def test_direct_constructor_rejects_naive_updated_at() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        ExchangeRateProvider(
            provider_id=value.provider_id,
            name=value.name,
            provider_type=value.provider_type,
            status=value.status,
            trust_level=value.trust_level,
            capabilities=value.capabilities,
            endpoint=value.endpoint,
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=datetime(
                2026,
                8,
                3,
                9,
                1,
            ),
            version=1,
        )


def test_updated_at_must_not_precede_created_at() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        ExchangeRateProvider(
            provider_id=value.provider_id,
            name=value.name,
            provider_type=value.provider_type,
            status=value.status,
            trust_level=value.trust_level,
            capabilities=value.capabilities,
            endpoint=value.endpoint,
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
def test_provider_rejects_invalid_version(
    version: int,
) -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        ExchangeRateProvider(
            provider_id=value.provider_id,
            name=value.name,
            provider_type=value.provider_type,
            status=value.status,
            trust_level=value.trust_level,
            capabilities=value.capabilities,
            endpoint=value.endpoint,
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
def test_provider_rejects_non_integer_version(
    version: object,
) -> None:
    value = provider()

    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        ExchangeRateProvider(
            provider_id=value.provider_id,
            name=value.name,
            provider_type=value.provider_type,
            status=value.status,
            trust_level=value.trust_level,
            capabilities=value.capabilities,
            endpoint=value.endpoint,
            metadata=value.metadata,
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=version,  # type: ignore[arg-type]
        )


def test_provider_rejects_sensitive_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        provider(
            metadata={
                "api_key": "secret",
            }
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://rates.example.com/v1",
        (
            "https://user:password@"
            "rates.example.com/v1"
        ),
        (
            "https://rates.example.com/v1"
            "?access_token=secret"
        ),
    ],
)
def test_provider_rejects_unsafe_endpoint(
    endpoint: str,
) -> None:
    with pytest.raises(ValueError):
        provider(endpoint=endpoint)


def test_provider_canonical_dict() -> None:
    payload = provider().canonical_dict()

    assert list(payload) == [
        "provider_id",
        "name",
        "provider_type",
        "status",
        "trust_level",
        "capabilities",
        "endpoint",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["provider_id"] == "provider-rba"
    assert payload["name"] == (
        "Reserve Bank of Australia"
    )
    assert payload["provider_type"] == (
        "central_bank"
    )
    assert payload["status"] == "active"
    assert payload["trust_level"] == (
        "authoritative"
    )
    assert payload["created_at"] == (
        "2026-08-03T09:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-03T09:00:00+00:00"
    )
    assert payload["version"] == 1


def test_provider_canonical_dict_contains_capabilities() -> None:
    payload = provider().canonical_dict()

    assert payload["capabilities"] == {
        "supported_currency_pairs": [
            "AUD/NZD",
            "AUD/USD",
        ],
        "supported_rate_source_types": [
            "central_bank_reference",
            "mid_market",
        ],
        "supports_streaming": False,
        "supports_historical_rates": True,
        "supports_inverse_rates": True,
        "maximum_staleness_seconds": 3600,
        "expected_latency_ms": 500,
        "expected_reliability": "0.999",
    }


def test_provider_canonical_dict_contains_endpoint() -> None:
    payload = provider().canonical_dict()

    assert payload["endpoint"] == {
        "url": (
            "https://rates.example.com/v1/reference"
        ),
        "description": (
            "Public reference-rate feed"
        ),
    }


def test_provider_canonical_dict_contains_metadata() -> None:
    payload = provider().canonical_dict()

    assert payload["metadata"] == {
        "audited": True,
        "data_region": "Australia",
        "jurisdiction": "AU",
    }


def test_provider_canonical_dict_is_fresh() -> None:
    value = provider()

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert (
        first["capabilities"]
        is not second["capabilities"]
    )
    assert first["endpoint"] is not second["endpoint"]
    assert first["metadata"] is not second["metadata"]


def test_provider_preserves_canonical_value_objects() -> None:
    provider_id = ExchangeRateProviderId(
        "provider-rba"
    )
    name = ProviderName(
        "Reserve Bank of Australia"
    )
    capabilities = ProviderCapabilities(
        supported_currency_pairs=("AUD/USD",)
    )
    endpoint = ProviderEndpoint.of(
        "https://rates.example.com/v1"
    )
    metadata = ProviderMetadata(
        {
            "jurisdiction": "AU",
        }
    )

    value = ExchangeRateProvider(
        provider_id=provider_id,
        name=name,
        provider_type=(
            ExchangeRateProviderType.CENTRAL_BANK
        ),
        status=ExchangeRateProviderStatus.ACTIVE,
        trust_level=(
            ProviderTrustLevel.AUTHORITATIVE
        ),
        capabilities=capabilities,
        endpoint=endpoint,
        metadata=metadata,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        version=1,
    )

    assert value.provider_id is provider_id
    assert value.name is name
    assert value.capabilities is capabilities
    assert value.endpoint is endpoint
    assert value.metadata is metadata


def test_provider_contains_no_rate_source_collection() -> None:
    value = provider()

    for forbidden in (
        "rate_sources",
        "sources",
        "source_registry",
        "register_source",
        "add_source",
    ):
        assert not hasattr(value, forbidden)


def test_provider_contains_no_runtime_authority() -> None:
    value = provider()

    for forbidden in (
        "request",
        "fetch",
        "connect",
        "stream",
        "lock_rate",
        "convert",
        "publish_rate",
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


def test_remaining_aggregates_not_added_yet() -> None:
    from afritech.novapay.domain import (
        exchange_rate_provider,
    )

    assert hasattr(
        exchange_rate_provider,
        "ExchangeRateProviderRegistry",
    )
