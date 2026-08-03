from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.exchange_rate_provider import (
    ExchangeRateProvider,
    ExchangeRateProviderRegistry,
    ExchangeRateProviderRegistryId,
    ExchangeRateProviderStatus,
    ExchangeRateProviderType,
    ProviderMetadata,
    ProviderTrustLevel,
    RateSource,
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


def provider(
    provider_id: str,
    *,
    name: str | None = None,
    provider_type: object = "aggregator",
    status: object = "active",
    trust_level: object = "trusted",
) -> ExchangeRateProvider:
    return ExchangeRateProvider.create(
        provider_id=provider_id,
        name=name or provider_id,
        provider_type=provider_type,
        status=status,
        trust_level=trust_level,
        capabilities={
            "supported_currency_pairs": (
                "AUD/USD",
            ),
            "supported_rate_source_types": (
                "spot",
                "composite",
            ),
            "maximum_staleness_seconds": 300,
        },
        created_at=CREATED_AT,
    )


def source(
    source_id: str,
    provider_id: str,
    *,
    source_type: object = "spot",
    status: object = "active",
    trust_level: object = "trusted",
    priority: int = 100,
    pairs: tuple[str, ...] = ("AUD/USD",),
) -> RateSource:
    return RateSource.create(
        rate_source_id=source_id,
        provider_id=provider_id,
        source_type=source_type,
        status=status,
        trust_level=trust_level,
        priority=priority,
        supported_currency_pairs=pairs,
        maximum_staleness_seconds=300,
        expected_latency_ms=250,
        expected_reliability=Decimal("0.99"),
        created_at=CREATED_AT,
    )


def registry(
    *,
    providers: tuple[ExchangeRateProvider, ...] = (),
    rate_sources: tuple[RateSource, ...] = (),
) -> ExchangeRateProviderRegistry:
    return ExchangeRateProviderRegistry.create(
        registry_id="registry-global-fx",
        providers=providers,
        rate_sources=rate_sources,
        metadata={
            "scope": "global",
        },
        created_at=CREATED_AT,
    )


def test_create_empty_registry() -> None:
    value = registry()

    assert value.registry_id == (
        ExchangeRateProviderRegistryId(
            "registry-global-fx"
        )
    )
    assert value.providers == ()
    assert value.rate_sources == ()
    assert value.metadata == ProviderMetadata(
        {
            "scope": "global",
        }
    )
    assert value.created_at == CREATED_AT
    assert value.updated_at == CREATED_AT
    assert value.version == 1


def test_registry_identifier_normalization() -> None:
    value = ExchangeRateProviderRegistry.create(
        registry_id=" registry-global-fx ",
        created_at=CREATED_AT,
    )

    assert value.registry_id.value == (
        "registry-global-fx"
    )
    assert value.registry_id.canonical() == (
        "registry-global-fx"
    )
    assert str(value.registry_id) == (
        "registry-global-fx"
    )


def test_registry_is_immutable() -> None:
    value = registry()

    with pytest.raises(FrozenInstanceError):
        value.version = 2  # type: ignore[misc]


def test_registry_uses_slots() -> None:
    assert not hasattr(registry(), "__dict__")


def test_registry_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(
            ExchangeRateProviderRegistry
        )
    } == {
        "registry_id",
        "providers",
        "rate_sources",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    }


def test_registry_orders_providers_by_identifier() -> None:
    provider_z = provider("provider-z")
    provider_a = provider("provider-a")
    provider_m = provider("provider-m")

    value = registry(
        providers=(
            provider_z,
            provider_a,
            provider_m,
        )
    )

    assert tuple(
        item.provider_id.value
        for item in value.providers
    ) == (
        "provider-a",
        "provider-m",
        "provider-z",
    )


def test_registry_orders_sources_deterministically() -> None:
    provider_a = provider("provider-a")
    provider_b = provider("provider-b")

    source_b = source(
        "source-b",
        "provider-b",
        priority=20,
    )
    source_a2 = source(
        "source-a2",
        "provider-a",
        priority=10,
    )
    source_a1 = source(
        "source-a1",
        "provider-a",
        priority=10,
    )

    value = registry(
        providers=(
            provider_b,
            provider_a,
        ),
        rate_sources=(
            source_b,
            source_a2,
            source_a1,
        ),
    )

    assert tuple(
        item.rate_source_id.value
        for item in value.rate_sources
    ) == (
        "source-a1",
        "source-a2",
        "source-b",
    )


def test_registry_rejects_duplicate_provider_ids() -> None:
    first = provider(
        "provider-001",
        name="Provider One",
    )
    duplicate = provider(
        "provider-001",
        name="Provider Duplicate",
    )

    with pytest.raises(
        ValueError,
        match="duplicate provider ids",
    ):
        registry(
            providers=(
                first,
                duplicate,
            )
        )


def test_registry_rejects_duplicate_source_ids() -> None:
    provider_value = provider("provider-001")

    first = source(
        "source-001",
        "provider-001",
        priority=10,
    )
    duplicate = source(
        "source-001",
        "provider-001",
        priority=20,
    )

    with pytest.raises(
        ValueError,
        match="duplicate rate-source ids",
    ):
        registry(
            providers=(provider_value,),
            rate_sources=(
                first,
                duplicate,
            ),
        )


def test_registry_rejects_orphan_source() -> None:
    orphan = source(
        "source-orphan",
        "provider-missing",
    )

    with pytest.raises(
        ValueError,
        match="without registered providers",
    ):
        registry(
            rate_sources=(orphan,)
        )


def test_get_and_require_provider() -> None:
    provider_value = provider("provider-001")

    value = registry(
        providers=(provider_value,)
    )

    assert value.get_provider(
        "provider-001"
    ) is provider_value

    assert value.require_provider(
        "provider-001"
    ) is provider_value

    assert value.get_provider(
        "provider-missing"
    ) is None

    with pytest.raises(
        LookupError,
        match="provider-missing",
    ):
        value.require_provider(
            "provider-missing"
        )


def test_get_and_require_rate_source() -> None:
    provider_value = provider("provider-001")
    source_value = source(
        "source-001",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(source_value,),
    )

    assert value.get_rate_source(
        "source-001"
    ) is source_value

    assert value.require_rate_source(
        "source-001"
    ) is source_value

    assert value.get_rate_source(
        "source-missing"
    ) is None

    with pytest.raises(
        LookupError,
        match="source-missing",
    ):
        value.require_rate_source(
            "source-missing"
        )


def test_provider_lookup_filters() -> None:
    central = provider(
        "provider-central",
        provider_type="central_bank",
        status="active",
        trust_level="authoritative",
    )
    aggregator = provider(
        "provider-aggregator",
        provider_type="aggregator",
        status="suspended",
        trust_level="trusted",
    )

    value = registry(
        providers=(
            central,
            aggregator,
        )
    )

    assert value.providers_by_status(
        ExchangeRateProviderStatus.ACTIVE
    ) == (
        central,
    )

    assert value.providers_by_type(
        ExchangeRateProviderType.CENTRAL_BANK
    ) == (
        central,
    )

    assert value.providers_by_trust_level(
        ProviderTrustLevel.TRUSTED
    ) == (
        aggregator,
    )


def test_rate_source_lookup_filters() -> None:
    provider_a = provider("provider-a")
    provider_b = provider("provider-b")

    spot = source(
        "source-spot",
        "provider-a",
        source_type="spot",
        status="active",
        trust_level="trusted",
        priority=10,
        pairs=(
            "AUD/USD",
            "USD/EUR",
        ),
    )
    composite = source(
        "source-composite",
        "provider-b",
        source_type="composite",
        status="suspended",
        trust_level="verified",
        priority=20,
        pairs=("AUD/USD",),
    )

    value = registry(
        providers=(
            provider_a,
            provider_b,
        ),
        rate_sources=(
            composite,
            spot,
        ),
    )

    assert value.sources_for_provider(
        "provider-a"
    ) == (
        spot,
    )

    assert value.sources_by_status(
        RateSourceStatus.ACTIVE
    ) == (
        spot,
    )

    assert value.sources_by_type(
        RateSourceType.SPOT
    ) == (
        spot,
    )

    assert value.sources_by_trust_level(
        ProviderTrustLevel.VERIFIED
    ) == (
        composite,
    )

    assert value.sources_supporting_pair(
        "AUD/USD"
    ) == (
        spot,
        composite,
    )

    assert value.active_sources_supporting_pair(
        "AUD/USD"
    ) == (
        spot,
    )


def test_registry_contains_no_runtime_authority() -> None:
    value = registry()

    for forbidden in (
        "request",
        "fetch",
        "connect",
        "stream",
        "publish_rate",
        "calculate_rate",
        "select_best_rate",
        "select_provider",
        "failover",
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


def test_registry_module_contract() -> None:
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


def at(minutes: int) -> datetime:
    return CREATED_AT + timedelta(minutes=minutes)


def test_register_provider_immutably() -> None:
    original = registry()
    provider_value = provider("provider-001")

    updated = original.register_provider(
        provider_value,
        occurred_at=at(1),
    )

    assert original.providers == ()
    assert updated.providers == (
        provider_value,
    )
    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_register_provider_rejects_duplicate() -> None:
    provider_value = provider("provider-001")
    value = registry(
        providers=(provider_value,)
    )

    with pytest.raises(
        ValueError,
        match="already contains provider",
    ):
        value.register_provider(
            provider_value,
            occurred_at=at(1),
        )


def test_register_provider_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match="ExchangeRateProvider",
    ):
        registry().register_provider(
            object(),  # type: ignore[arg-type]
            occurred_at=at(1),
        )


def test_register_rate_source_immutably() -> None:
    provider_value = provider("provider-001")
    source_value = source(
        "source-001",
        "provider-001",
    )

    original = registry(
        providers=(provider_value,)
    )

    updated = original.register_rate_source(
        source_value,
        occurred_at=at(1),
    )

    assert original.rate_sources == ()
    assert updated.rate_sources == (
        source_value,
    )
    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_register_rate_source_rejects_duplicate() -> None:
    provider_value = provider("provider-001")
    source_value = source(
        "source-001",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(source_value,),
    )

    with pytest.raises(
        ValueError,
        match="already contains rate source",
    ):
        value.register_rate_source(
            source_value,
            occurred_at=at(1),
        )


def test_register_rate_source_rejects_orphan() -> None:
    orphan = source(
        "source-orphan",
        "provider-missing",
    )

    with pytest.raises(
        ValueError,
        match="provider is not registered",
    ):
        registry().register_rate_source(
            orphan,
            occurred_at=at(1),
        )


def test_register_rate_source_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match="RateSource",
    ):
        registry().register_rate_source(
            object(),  # type: ignore[arg-type]
            occurred_at=at(1),
        )


def test_update_provider_immutably() -> None:
    original_provider = provider("provider-001")

    value = registry(
        providers=(original_provider,)
    )

    updated_provider = (
        original_provider.update_trust_level(
            "authoritative",
            occurred_at=at(1),
        )
    )

    updated = value.update_provider(
        updated_provider,
        occurred_at=at(1),
    )

    assert value.require_provider(
        "provider-001"
    ) is original_provider

    assert updated.require_provider(
        "provider-001"
    ) is updated_provider

    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_update_provider_rejects_missing() -> None:
    missing = provider("provider-missing")

    with pytest.raises(
        LookupError,
        match="provider-missing",
    ):
        registry().update_provider(
            missing,
            occurred_at=at(1),
        )


def test_update_provider_rejects_noop() -> None:
    provider_value = provider("provider-001")

    value = registry(
        providers=(provider_value,)
    )

    with pytest.raises(
        ValueError,
        match="must change provider",
    ):
        value.update_provider(
            provider_value,
            occurred_at=at(1),
        )


def test_update_provider_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match="ExchangeRateProvider",
    ):
        registry().update_provider(
            object(),  # type: ignore[arg-type]
            occurred_at=at(1),
        )


def test_update_rate_source_immutably() -> None:
    provider_value = provider("provider-001")

    original_source = source(
        "source-001",
        "provider-001",
        priority=100,
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(original_source,),
    )

    updated_source = original_source.update_priority(
        1,
        occurred_at=at(1),
    )

    updated = value.update_rate_source(
        updated_source,
        occurred_at=at(1),
    )

    assert value.require_rate_source(
        "source-001"
    ) is original_source

    assert updated.require_rate_source(
        "source-001"
    ) is updated_source

    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_update_rate_source_rejects_missing() -> None:
    provider_value = provider("provider-001")

    missing = source(
        "source-missing",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,)
    )

    with pytest.raises(
        LookupError,
        match="source-missing",
    ):
        value.update_rate_source(
            missing,
            occurred_at=at(1),
        )


def test_update_rate_source_rejects_orphan_linkage() -> None:
    provider_value = provider("provider-001")

    original = source(
        "source-001",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(original,),
    )

    orphan_replacement = RateSource.create(
        rate_source_id="source-001",
        provider_id="provider-missing",
        source_type="spot",
        status="active",
        trust_level="trusted",
        priority=10,
        supported_currency_pairs=("AUD/USD",),
        created_at=CREATED_AT,
    )

    with pytest.raises(
        ValueError,
        match="provider is not registered",
    ):
        value.update_rate_source(
            orphan_replacement,
            occurred_at=at(1),
        )


def test_update_rate_source_rejects_noop() -> None:
    provider_value = provider("provider-001")

    source_value = source(
        "source-001",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(source_value,),
    )

    with pytest.raises(
        ValueError,
        match="must change rate source",
    ):
        value.update_rate_source(
            source_value,
            occurred_at=at(1),
        )


def test_update_rate_source_rejects_wrong_type() -> None:
    with pytest.raises(
        TypeError,
        match="RateSource",
    ):
        registry().update_rate_source(
            object(),  # type: ignore[arg-type]
            occurred_at=at(1),
        )


def test_registry_update_metadata() -> None:
    updated = registry().update_metadata(
        {
            "scope": "global",
            "reviewed": True,
        },
        occurred_at=at(1),
    )

    assert updated.metadata == ProviderMetadata(
        {
            "scope": "global",
            "reviewed": True,
        }
    )
    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_registry_rejects_noop_metadata_update() -> None:
    value = registry()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        value.update_metadata(
            value.metadata,
            occurred_at=at(1),
        )


def test_registry_rejects_backdated_change() -> None:
    provider_value = provider("provider-001")

    value = registry().register_provider(
        provider_value,
        occurred_at=at(2),
    )

    with pytest.raises(
        ValueError,
        match="must not be earlier than updated_at",
    ):
        value.update_metadata(
            {
                "reviewed": True,
            },
            occurred_at=at(1),
        )


def test_registry_allows_same_timestamp_change() -> None:
    provider_value = provider("provider-001")

    value = registry().register_provider(
        provider_value,
        occurred_at=at(1),
    )

    updated = value.update_metadata(
        {
            "reviewed": True,
        },
        occurred_at=at(1),
    )

    assert updated.updated_at == at(1)
    assert updated.version == 3


def test_registry_version_chain() -> None:
    provider_value = provider("provider-001")

    source_value = source(
        "source-001",
        "provider-001",
    )

    value = registry()
    assert value.version == 1

    value = value.register_provider(
        provider_value,
        occurred_at=at(1),
    )
    assert value.version == 2

    value = value.register_rate_source(
        source_value,
        occurred_at=at(2),
    )
    assert value.version == 3

    updated_provider = (
        provider_value.update_trust_level(
            "authoritative",
            occurred_at=at(3),
        )
    )

    value = value.update_provider(
        updated_provider,
        occurred_at=at(3),
    )
    assert value.version == 4

    updated_source = source_value.update_priority(
        1,
        occurred_at=at(4),
    )

    value = value.update_rate_source(
        updated_source,
        occurred_at=at(4),
    )
    assert value.version == 5

    value = value.update_metadata(
        {
            "reviewed": True,
        },
        occurred_at=at(5),
    )
    assert value.version == 6


def test_registry_rejects_naive_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        ExchangeRateProviderRegistry.create(
            registry_id="registry-001",
            created_at=datetime(
                2026,
                8,
                3,
                0,
                0,
            ),
        )


def test_registry_rejects_naive_change_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        registry().update_metadata(
            {
                "reviewed": True,
            },
            occurred_at=datetime(
                2026,
                8,
                3,
                0,
                1,
            ),
        )


def test_registry_canonical_dict() -> None:
    provider_value = provider("provider-001")

    source_value = source(
        "source-001",
        "provider-001",
    )

    payload = registry(
        providers=(provider_value,),
        rate_sources=(source_value,),
    ).canonical_dict()

    assert list(payload) == [
        "registry_id",
        "providers",
        "rate_sources",
        "metadata",
        "created_at",
        "updated_at",
        "version",
    ]

    assert payload["registry_id"] == (
        "registry-global-fx"
    )
    assert len(payload["providers"]) == 1
    assert len(payload["rate_sources"]) == 1
    assert payload["metadata"] == {
        "scope": "global",
    }
    assert payload["created_at"] == (
        "2026-08-03T00:00:00+00:00"
    )
    assert payload["updated_at"] == (
        "2026-08-03T00:00:00+00:00"
    )
    assert payload["version"] == 1


def test_registry_canonical_dict_is_fresh() -> None:
    provider_value = provider("provider-001")

    source_value = source(
        "source-001",
        "provider-001",
    )

    value = registry(
        providers=(provider_value,),
        rate_sources=(source_value,),
    )

    first = value.canonical_dict()
    second = value.canonical_dict()

    assert first == second
    assert first is not second
    assert first["providers"] is not second["providers"]
    assert first["rate_sources"] is not second["rate_sources"]
    assert first["metadata"] is not second["metadata"]
