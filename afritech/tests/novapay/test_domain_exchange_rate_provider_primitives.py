from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from enum import Enum
from types import MappingProxyType

import pytest

from afritech.novapay.domain.exchange_rate_provider import (
    ExchangeRateProviderId,
    ExchangeRateProviderStatus,
    ExchangeRateProviderType,
    ProviderCapabilities,
    ProviderEndpoint,
    ProviderMetadata,
    ProviderName,
    ProviderTrustLevel,
    RateSourceId,
    RateSourceMetadata,
    RateSourceStatus,
    RateSourceType,
)


@pytest.mark.parametrize(
    ("identifier_type", "raw", "expected"),
    [
        (
            ExchangeRateProviderId,
            " provider-rba ",
            "provider-rba",
        ),
        (
            RateSourceId,
            " source-rba-aud ",
            "source-rba-aud",
        ),
    ],
)
def test_identifier_normalization(
    identifier_type: object,
    raw: str,
    expected: str,
) -> None:
    value = identifier_type.of(raw)  # type: ignore[attr-defined]

    assert value.value == expected
    assert value.canonical() == expected
    assert str(value) == expected


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateProviderId,
        RateSourceId,
    ],
)
def test_identifier_is_immutable(
    identifier_type: object,
) -> None:
    value = identifier_type("identifier-001")  # type: ignore[operator]

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateProviderId,
        RateSourceId,
    ],
)
@pytest.mark.parametrize(
    "raw",
    [
        "",
        " ",
    ],
)
def test_identifier_rejects_empty_value(
    identifier_type: object,
    raw: str,
) -> None:
    with pytest.raises(ValueError):
        identifier_type(raw)  # type: ignore[operator]


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateProviderId,
        RateSourceId,
    ],
)
@pytest.mark.parametrize(
    "raw",
    [
        None,
        123,
        True,
    ],
)
def test_identifier_rejects_non_string(
    identifier_type: object,
    raw: object,
) -> None:
    with pytest.raises(TypeError):
        identifier_type.of(raw)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateProviderStatus,
        ExchangeRateProviderType,
        RateSourceStatus,
        RateSourceType,
        ProviderTrustLevel,
    ],
)
def test_provider_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


@pytest.mark.parametrize(
    ("enum_type", "raw", "expected"),
    [
        (
            ExchangeRateProviderStatus,
            " DEGRADED ",
            ExchangeRateProviderStatus.DEGRADED,
        ),
        (
            ExchangeRateProviderType,
            " central-bank ",
            ExchangeRateProviderType.CENTRAL_BANK,
        ),
        (
            RateSourceStatus,
            " suspended ",
            RateSourceStatus.SUSPENDED,
        ),
        (
            RateSourceType,
            " mid market ",
            RateSourceType.MID_MARKET,
        ),
        (
            ProviderTrustLevel,
            " authoritative ",
            ProviderTrustLevel.AUTHORITATIVE,
        ),
    ],
)
def test_provider_enums_parse_normalized_values(
    enum_type: object,
    raw: str,
    expected: object,
) -> None:
    assert enum_type.parse(raw) is expected  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateProviderStatus,
        ExchangeRateProviderType,
        RateSourceStatus,
        RateSourceType,
        ProviderTrustLevel,
    ],
)
def test_provider_enums_reject_unknown_value(
    enum_type: object,
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse("unknown-value")  # type: ignore[attr-defined]


def test_provider_name_normalizes_whitespace() -> None:
    name = ProviderName.of(
        " Reserve   Bank of Australia "
    )

    assert name.value == "Reserve Bank of Australia"
    assert name.canonical() == "Reserve Bank of Australia"
    assert str(name) == "Reserve Bank of Australia"


def test_provider_name_is_immutable() -> None:
    name = ProviderName("Provider")

    with pytest.raises(FrozenInstanceError):
        name.value = "Changed"  # type: ignore[misc]


def test_provider_endpoint_normalizes() -> None:
    endpoint = ProviderEndpoint.of(
        " HTTPS://RATES.EXAMPLE.COM/v1/rates/ ",
        description=" Public rate feed ",
    )

    assert endpoint.url == (
        "https://rates.example.com/v1/rates"
    )
    assert endpoint.hostname == "rates.example.com"
    assert endpoint.description == "Public rate feed"


def test_provider_endpoint_supports_explicit_port() -> None:
    endpoint = ProviderEndpoint.of(
        "https://rates.example.com:8443/v1"
    )

    assert endpoint.url == (
        "https://rates.example.com:8443/v1"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://rates.example.com/v1",
        "ftp://rates.example.com/v1",
        "rates.example.com/v1",
    ],
)
def test_provider_endpoint_requires_https(
    url: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="HTTPS",
    ):
        ProviderEndpoint.of(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@rates.example.com/v1",
        "https://rates.example.com/v1?api_key=secret",
        "https://rates.example.com/v1#token",
    ],
)
def test_provider_endpoint_rejects_sensitive_url_parts(
    url: str,
) -> None:
    with pytest.raises(ValueError):
        ProviderEndpoint.of(url)


def test_provider_endpoint_canonical_dict() -> None:
    endpoint = ProviderEndpoint.of(
        "https://rates.example.com/v1",
        description="Rates",
    )

    assert endpoint.canonical_dict() == {
        "url": "https://rates.example.com/v1",
        "description": "Rates",
    }


def test_provider_capabilities_normalize() -> None:
    capabilities = ProviderCapabilities(
        supported_currency_pairs=(
            "usd/eur",
            "AUD/USD",
        ),
        supported_rate_source_types=(
            "spot",
            RateSourceType.MID_MARKET,
        ),
        supports_streaming=True,
        supports_historical_rates=True,
        supports_inverse_rates=True,
        maximum_staleness_seconds=60,
        expected_latency_ms=250,
        expected_reliability=Decimal("0.995"),
    )

    assert capabilities.supported_currency_pairs == (
        "AUD/USD",
        "USD/EUR",
    )
    assert capabilities.supported_rate_source_types == (
        RateSourceType.MID_MARKET,
        RateSourceType.SPOT,
    )
    assert capabilities.expected_reliability == (
        Decimal("0.995")
    )


def test_provider_capabilities_from_mapping() -> None:
    capabilities = ProviderCapabilities.of(
        {
            "supported_currency_pairs": [
                "AUD/USD",
            ],
            "supported_rate_source_types": [
                "spot",
            ],
            "supports_streaming": True,
            "maximum_staleness_seconds": 120,
        }
    )

    assert capabilities.supports_pair("aud/usd")
    assert capabilities.supports_source_type("spot")
    assert capabilities.supports_streaming is True


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
def test_provider_capabilities_reject_invalid_pair(
    pair: str,
) -> None:
    with pytest.raises(ValueError):
        ProviderCapabilities(
            supported_currency_pairs=(pair,)
        )


def test_provider_capabilities_reject_duplicate_pairs() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        ProviderCapabilities(
            supported_currency_pairs=(
                "AUD/USD",
                "AUD/USD",
            )
        )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_provider_capabilities_reject_invalid_staleness(
    value: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than 0",
    ):
        ProviderCapabilities(
            maximum_staleness_seconds=value
        )


@pytest.mark.parametrize(
    "value",
    [
        Decimal("-0.01"),
        Decimal("1.01"),
    ],
)
def test_provider_capabilities_reject_invalid_reliability(
    value: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):
        ProviderCapabilities(
            expected_reliability=value
        )


def test_provider_capabilities_reject_float_reliability() -> None:
    with pytest.raises(
        TypeError,
        match="must not be constructed from float",
    ):
        ProviderCapabilities(
            expected_reliability=0.99
        )


def test_provider_capabilities_canonical_dict() -> None:
    capabilities = ProviderCapabilities(
        supported_currency_pairs=("AUD/USD",),
        supported_rate_source_types=("spot",),
        supports_streaming=True,
        maximum_staleness_seconds=60,
        expected_latency_ms=300,
        expected_reliability=Decimal("0.99"),
    )

    assert capabilities.canonical_dict() == {
        "supported_currency_pairs": ["AUD/USD"],
        "supported_rate_source_types": ["spot"],
        "supports_streaming": True,
        "supports_historical_rates": False,
        "supports_inverse_rates": False,
        "maximum_staleness_seconds": 60,
        "expected_latency_ms": 300,
        "expected_reliability": "0.99",
    }


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
def test_metadata_normalizes_keys(
    metadata_type: object,
) -> None:
    metadata = metadata_type(  # type: ignore[operator]
        {
            " Data Region ": "Australia",
            " Audited ": True,
        }
    )

    assert metadata.values == {
        "audited": True,
        "data_region": "Australia",
    }
    assert isinstance(
        metadata.values,
        MappingProxyType,
    )


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
def test_metadata_is_defensive(
    metadata_type: object,
) -> None:
    source = {
        "region": "Australia",
    }

    metadata = metadata_type(source)  # type: ignore[operator]
    source["region"] = "Changed"

    assert metadata.values == {
        "region": "Australia",
    }


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
def test_metadata_updates_immutably(
    metadata_type: object,
) -> None:
    original = metadata_type(  # type: ignore[operator]
        {
            "region": "Australia",
        }
    )

    updated = original.with_updates(
        {
            "reviewed": True,
        }
    )

    assert original.values == {
        "region": "Australia",
    }
    assert updated.values == {
        "region": "Australia",
        "reviewed": True,
    }


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "access_token",
        "client_secret",
        "password",
        "private_key",
        "credentials",
    ],
)
def test_metadata_rejects_sensitive_keys(
    metadata_type: object,
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        metadata_type(  # type: ignore[operator]
            {
                key: "secret",
            }
        )


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
def test_metadata_rejects_float_values(
    metadata_type: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="float",
    ):
        metadata_type(  # type: ignore[operator]
            {
                "reliability": 0.99,
            }
        )


@pytest.mark.parametrize(
    "metadata_type",
    [
        ProviderMetadata,
        RateSourceMetadata,
    ],
)
def test_metadata_rejects_unsupported_values(
    metadata_type: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="unsupported value type",
    ):
        metadata_type(  # type: ignore[operator]
            {
                "unsupported": object(),
            }
        )


def test_exact_provider_capability_field_contract() -> None:
    assert {
        item.name
        for item in fields(ProviderCapabilities)
    } == {
        "supported_currency_pairs",
        "supported_rate_source_types",
        "supports_streaming",
        "supports_historical_rates",
        "supports_inverse_rates",
        "maximum_staleness_seconds",
        "expected_latency_ms",
        "expected_reliability",
    }


def test_primitives_have_no_runtime_authority() -> None:
    values = (
        ProviderEndpoint.of(
            "https://rates.example.com/v1"
        ),
        ProviderCapabilities(),
        ProviderMetadata(),
        RateSourceMetadata(),
    )

    for value in values:
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


def test_provider_aggregate_is_available_in_module() -> None:
    from afritech.novapay.domain import (
        exchange_rate_provider,
    )

    assert hasattr(
        exchange_rate_provider,
        "ExchangeRateProvider",
    )


def test_remaining_aggregates_not_added_yet() -> None:
    from afritech.novapay.domain import (
        exchange_rate_provider,
    )

    assert hasattr(
        exchange_rate_provider,
        "ExchangeRateProviderRegistry",
    )
