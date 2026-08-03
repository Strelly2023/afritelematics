from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.exchange_rate_provider import (
    ExchangeRateProvider,
    ExchangeRateProviderId,
    ExchangeRateProviderStatus,
    ProviderCapabilities,
    ProviderEndpoint,
    ProviderMetadata,
    ProviderName,
    ProviderTrustLevel,
    RateSource,
    RateSourceId,
    RateSourceMetadata,
    RateSourceStatus,
)


CREATED_AT = datetime(
    2026,
    8,
    3,
    0,
    0,
    tzinfo=timezone.utc,
)


def at(minutes: int) -> datetime:
    return CREATED_AT + timedelta(minutes=minutes)


def provider(
    *,
    status: object = "draft",
) -> ExchangeRateProvider:
    return ExchangeRateProvider.create(
        provider_id="provider-rba",
        name="Reserve Bank of Australia",
        provider_type="central_bank",
        status=status,
        trust_level="verified",
        capabilities={
            "supported_currency_pairs": (
                "AUD/USD",
            ),
            "supported_rate_source_types": (
                "central_bank_reference",
            ),
            "maximum_staleness_seconds": 3600,
        },
        endpoint=(
            "https://rates.example.com/v1/reference"
        ),
        endpoint_description="Reference feed",
        metadata={
            "jurisdiction": "AU",
        },
        created_at=CREATED_AT,
    )


def rate_source(
    *,
    status: object = "draft",
) -> RateSource:
    return RateSource.create(
        rate_source_id="source-rba-reference",
        provider_id="provider-rba",
        source_type="central_bank_reference",
        status=status,
        trust_level="verified",
        priority=10,
        supported_currency_pairs=(
            "AUD/USD",
        ),
        maximum_staleness_seconds=3600,
        expected_latency_ms=500,
        expected_reliability=Decimal("0.99"),
        metadata={
            "jurisdiction": "AU",
        },
        created_at=CREATED_AT,
    )


def test_provider_draft_to_active() -> None:
    original = provider()

    updated = original.activate(
        occurred_at=at(1),
        reason="provider approved",
    )

    assert original.status is (
        ExchangeRateProviderStatus.DRAFT
    )
    assert updated.status is (
        ExchangeRateProviderStatus.ACTIVE
    )
    assert updated.version == 2
    assert updated.updated_at == at(1)


def test_provider_draft_to_retired() -> None:
    updated = provider().retire(
        occurred_at=at(1),
        reason="provider withdrawn",
    )

    assert updated.status is (
        ExchangeRateProviderStatus.RETIRED
    )
    assert updated.is_terminal is True


def test_provider_active_to_degraded() -> None:
    active = provider().activate(
        occurred_at=at(1),
        reason="approved",
    )

    degraded = active.mark_degraded(
        occurred_at=at(2),
        reason="high latency",
    )

    assert degraded.status is (
        ExchangeRateProviderStatus.DEGRADED
    )
    assert degraded.version == 3


def test_provider_active_to_suspended() -> None:
    active = provider().activate(
        occurred_at=at(1),
        reason="approved",
    )

    suspended = active.suspend(
        occurred_at=at(2),
        reason="maintenance",
    )

    assert suspended.status is (
        ExchangeRateProviderStatus.SUSPENDED
    )


def test_provider_degraded_to_active() -> None:
    degraded = (
        provider()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .mark_degraded(
            occurred_at=at(2),
            reason="latency",
        )
    )

    restored = degraded.activate(
        occurred_at=at(3),
        reason="recovered",
    )

    assert restored.status is (
        ExchangeRateProviderStatus.ACTIVE
    )


def test_provider_degraded_to_suspended() -> None:
    degraded = (
        provider()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .mark_degraded(
            occurred_at=at(2),
            reason="latency",
        )
    )

    suspended = degraded.suspend(
        occurred_at=at(3),
        reason="investigation",
    )

    assert suspended.status is (
        ExchangeRateProviderStatus.SUSPENDED
    )


def test_provider_suspended_to_active() -> None:
    suspended = (
        provider()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .suspend(
            occurred_at=at(2),
            reason="maintenance",
        )
    )

    restored = suspended.activate(
        occurred_at=at(3),
        reason="maintenance complete",
    )

    assert restored.status is (
        ExchangeRateProviderStatus.ACTIVE
    )


@pytest.mark.parametrize(
    ("starting_status", "operation"),
    [
        (
            "draft",
            "mark_degraded",
        ),
        (
            "draft",
            "suspend",
        ),
        (
            "active",
            "activate",
        ),
        (
            "degraded",
            "mark_degraded",
        ),
        (
            "suspended",
            "suspend",
        ),
    ],
)
def test_provider_rejects_invalid_transition(
    starting_status: str,
    operation: str,
) -> None:
    value = provider(status=starting_status)

    method = getattr(value, operation)

    with pytest.raises(
        ValueError,
        match="invalid exchange-rate provider status transition",
    ):
        method(
            occurred_at=at(1),
            reason="invalid transition",
        )


@pytest.mark.parametrize(
    "operation",
    [
        "activate",
        "mark_degraded",
        "suspend",
        "retire",
    ],
)
def test_provider_retired_is_terminal(
    operation: str,
) -> None:
    retired = provider().retire(
        occurred_at=at(1),
        reason="retired",
    )

    method = getattr(retired, operation)

    with pytest.raises(
        ValueError,
        match="invalid exchange-rate provider status transition",
    ):
        method(
            occurred_at=at(2),
            reason="invalid",
        )


def test_provider_lifecycle_metadata() -> None:
    updated = provider().activate(
        occurred_at=at(1),
        reason="provider approved",
        metadata={
            "approved_by": "treasury",
        },
    )

    assert updated.metadata.values == {
        "approved_by": "treasury",
        "current_status": "active",
        "jurisdiction": "AU",
        "lifecycle_reason": "provider approved",
        "previous_status": "draft",
    }


def test_provider_lifecycle_preserves_identity() -> None:
    original = provider()

    updated = original.activate(
        occurred_at=at(1),
        reason="approved",
    )

    assert updated.provider_id is original.provider_id
    assert updated.name is original.name
    assert updated.created_at == original.created_at


def test_provider_update_name() -> None:
    original = provider()

    updated = original.update_name(
        "RBA Reference Service",
        occurred_at=at(1),
    )

    assert original.name == ProviderName(
        "Reserve Bank of Australia"
    )
    assert updated.name == ProviderName(
        "RBA Reference Service"
    )
    assert updated.version == 2


def test_provider_rejects_noop_name_update() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="must change name",
    ):
        value.update_name(
            value.name,
            occurred_at=at(1),
        )


def test_provider_update_endpoint() -> None:
    value = provider()

    updated = value.update_endpoint(
        "https://rates.example.com/v2/reference",
        description="Version 2 feed",
        occurred_at=at(1),
    )

    assert updated.endpoint == ProviderEndpoint.of(
        "https://rates.example.com/v2/reference",
        description="Version 2 feed",
    )


def test_provider_rejects_noop_endpoint_update() -> None:
    value = provider()

    assert value.endpoint is not None

    with pytest.raises(
        ValueError,
        match="must change endpoint",
    ):
        value.update_endpoint(
            value.endpoint.url,
            description=value.endpoint.description,
            occurred_at=at(1),
        )


def test_provider_remove_endpoint() -> None:
    updated = provider().remove_endpoint(
        occurred_at=at(1)
    )

    assert updated.endpoint is None


def test_provider_rejects_removing_missing_endpoint() -> None:
    value = ExchangeRateProvider.create(
        provider_id="provider-no-endpoint",
        name="Provider Without Endpoint",
        provider_type="aggregator",
        created_at=CREATED_AT,
    )

    with pytest.raises(
        ValueError,
        match="has no endpoint",
    ):
        value.remove_endpoint(
            occurred_at=at(1)
        )


def test_provider_update_capabilities() -> None:
    value = provider()

    updated = value.update_capabilities(
        {
            "supported_currency_pairs": (
                "AUD/USD",
                "AUD/NZD",
            ),
            "supported_rate_source_types": (
                "central_bank_reference",
            ),
            "maximum_staleness_seconds": 1800,
        },
        occurred_at=at(1),
    )

    assert updated.capabilities == ProviderCapabilities(
        supported_currency_pairs=(
            "AUD/NZD",
            "AUD/USD",
        ),
        supported_rate_source_types=(
            "central_bank_reference",
        ),
        maximum_staleness_seconds=1800,
    )


def test_provider_rejects_noop_capabilities_update() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="must change capabilities",
    ):
        value.update_capabilities(
            value.capabilities,
            occurred_at=at(1),
        )


def test_provider_update_trust_level() -> None:
    updated = provider().update_trust_level(
        "trusted",
        occurred_at=at(1),
    )

    assert updated.trust_level is (
        ProviderTrustLevel.TRUSTED
    )


def test_provider_rejects_noop_trust_update() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="must change trust level",
    ):
        value.update_trust_level(
            value.trust_level,
            occurred_at=at(1),
        )


def test_provider_update_metadata() -> None:
    updated = provider().update_metadata(
        {
            "jurisdiction": "AU",
            "reviewed": True,
        },
        occurred_at=at(1),
    )

    assert updated.metadata == ProviderMetadata(
        {
            "jurisdiction": "AU",
            "reviewed": True,
        }
    )


def test_provider_rejects_noop_metadata_update() -> None:
    value = provider()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        value.update_metadata(
            value.metadata,
            occurred_at=at(1),
        )


def test_provider_rejects_backdated_change() -> None:
    value = provider().activate(
        occurred_at=at(2),
        reason="approved",
    )

    with pytest.raises(
        ValueError,
        match="must not be earlier than updated_at",
    ):
        value.update_name(
            "Backdated Name",
            occurred_at=at(1),
        )


def test_provider_allows_same_timestamp_change() -> None:
    value = provider().activate(
        occurred_at=at(1),
        reason="approved",
    )

    updated = value.update_name(
        "RBA Service",
        occurred_at=at(1),
    )

    assert updated.updated_at == at(1)
    assert updated.version == 3


def test_provider_update_chain_versions() -> None:
    value = provider()

    value = value.activate(
        occurred_at=at(1),
        reason="approved",
    )
    assert value.version == 2

    value = value.update_name(
        "RBA Service",
        occurred_at=at(2),
    )
    assert value.version == 3

    value = value.update_trust_level(
        "trusted",
        occurred_at=at(3),
    )
    assert value.version == 4

    value = value.update_metadata(
        {
            "reviewed": True,
        },
        occurred_at=at(4),
    )
    assert value.version == 5


def test_rate_source_draft_to_active() -> None:
    original = rate_source()

    updated = original.activate(
        occurred_at=at(1),
        reason="source approved",
    )

    assert original.status is RateSourceStatus.DRAFT
    assert updated.status is RateSourceStatus.ACTIVE
    assert updated.version == 2


def test_rate_source_draft_to_retired() -> None:
    updated = rate_source().retire(
        occurred_at=at(1),
        reason="source withdrawn",
    )

    assert updated.status is RateSourceStatus.RETIRED
    assert updated.is_terminal is True


def test_rate_source_active_to_degraded() -> None:
    active = rate_source().activate(
        occurred_at=at(1),
        reason="approved",
    )

    degraded = active.mark_degraded(
        occurred_at=at(2),
        reason="delayed publication",
    )

    assert degraded.status is RateSourceStatus.DEGRADED


def test_rate_source_active_to_suspended() -> None:
    active = rate_source().activate(
        occurred_at=at(1),
        reason="approved",
    )

    suspended = active.suspend(
        occurred_at=at(2),
        reason="maintenance",
    )

    assert suspended.status is RateSourceStatus.SUSPENDED


def test_rate_source_degraded_to_active() -> None:
    degraded = (
        rate_source()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .mark_degraded(
            occurred_at=at(2),
            reason="delayed",
        )
    )

    restored = degraded.activate(
        occurred_at=at(3),
        reason="recovered",
    )

    assert restored.status is RateSourceStatus.ACTIVE


def test_rate_source_degraded_to_suspended() -> None:
    degraded = (
        rate_source()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .mark_degraded(
            occurred_at=at(2),
            reason="delayed",
        )
    )

    suspended = degraded.suspend(
        occurred_at=at(3),
        reason="investigation",
    )

    assert suspended.status is RateSourceStatus.SUSPENDED


def test_rate_source_suspended_to_active() -> None:
    suspended = (
        rate_source()
        .activate(
            occurred_at=at(1),
            reason="approved",
        )
        .suspend(
            occurred_at=at(2),
            reason="maintenance",
        )
    )

    restored = suspended.activate(
        occurred_at=at(3),
        reason="maintenance complete",
    )

    assert restored.status is RateSourceStatus.ACTIVE


@pytest.mark.parametrize(
    ("starting_status", "operation"),
    [
        (
            "draft",
            "mark_degraded",
        ),
        (
            "draft",
            "suspend",
        ),
        (
            "active",
            "activate",
        ),
        (
            "degraded",
            "mark_degraded",
        ),
        (
            "suspended",
            "suspend",
        ),
    ],
)
def test_rate_source_rejects_invalid_transition(
    starting_status: str,
    operation: str,
) -> None:
    value = rate_source(status=starting_status)

    method = getattr(value, operation)

    with pytest.raises(
        ValueError,
        match="invalid rate-source status transition",
    ):
        method(
            occurred_at=at(1),
            reason="invalid transition",
        )


@pytest.mark.parametrize(
    "operation",
    [
        "activate",
        "mark_degraded",
        "suspend",
        "retire",
    ],
)
def test_rate_source_retired_is_terminal(
    operation: str,
) -> None:
    retired = rate_source().retire(
        occurred_at=at(1),
        reason="retired",
    )

    method = getattr(retired, operation)

    with pytest.raises(
        ValueError,
        match="invalid rate-source status transition",
    ):
        method(
            occurred_at=at(2),
            reason="invalid",
        )


def test_rate_source_lifecycle_metadata() -> None:
    updated = rate_source().activate(
        occurred_at=at(1),
        reason="source approved",
        metadata={
            "approved_by": "treasury",
        },
    )

    assert updated.metadata.values == {
        "approved_by": "treasury",
        "current_status": "active",
        "jurisdiction": "AU",
        "lifecycle_reason": "source approved",
        "previous_status": "draft",
    }


def test_rate_source_lifecycle_preserves_identity() -> None:
    original = rate_source()

    updated = original.activate(
        occurred_at=at(1),
        reason="approved",
    )

    assert (
        updated.rate_source_id
        is original.rate_source_id
    )
    assert updated.provider_id is original.provider_id
    assert updated.created_at == original.created_at


def test_rate_source_update_priority() -> None:
    original = rate_source()

    updated = original.update_priority(
        5,
        occurred_at=at(1),
    )

    assert original.priority == 10
    assert updated.priority == 5
    assert updated.version == 2


def test_rate_source_rejects_noop_priority_update() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must change priority",
    ):
        value.update_priority(
            value.priority,
            occurred_at=at(1),
        )


def test_rate_source_update_pairs() -> None:
    updated = rate_source().update_supported_currency_pairs(
        (
            "AUD/USD",
            "AUD/NZD",
        ),
        occurred_at=at(1),
    )

    assert updated.supported_currency_pairs == (
        "AUD/NZD",
        "AUD/USD",
    )


def test_rate_source_rejects_noop_pair_update() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must change supported pairs",
    ):
        value.update_supported_currency_pairs(
            value.supported_currency_pairs,
            occurred_at=at(1),
        )


def test_rate_source_update_freshness_policy() -> None:
    updated = rate_source().update_freshness_policy(
        maximum_staleness_seconds=120,
        expected_latency_ms=250,
        expected_reliability=Decimal("0.999"),
        occurred_at=at(1),
    )

    assert updated.maximum_staleness_seconds == 120
    assert updated.expected_latency_ms == 250
    assert updated.expected_reliability == (
        Decimal("0.999")
    )


def test_rate_source_rejects_noop_freshness_update() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must change policy",
    ):
        value.update_freshness_policy(
            maximum_staleness_seconds=(
                value.maximum_staleness_seconds
            ),
            expected_latency_ms=value.expected_latency_ms,
            expected_reliability=(
                value.expected_reliability
            ),
            occurred_at=at(1),
        )


def test_rate_source_update_trust_level() -> None:
    updated = rate_source().update_trust_level(
        "trusted",
        occurred_at=at(1),
    )

    assert updated.trust_level is (
        ProviderTrustLevel.TRUSTED
    )


def test_rate_source_rejects_noop_trust_update() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must change trust level",
    ):
        value.update_trust_level(
            value.trust_level,
            occurred_at=at(1),
        )


def test_rate_source_update_metadata() -> None:
    updated = rate_source().update_metadata(
        {
            "jurisdiction": "AU",
            "reviewed": True,
        },
        occurred_at=at(1),
    )

    assert updated.metadata == RateSourceMetadata(
        {
            "jurisdiction": "AU",
            "reviewed": True,
        }
    )


def test_rate_source_rejects_noop_metadata_update() -> None:
    value = rate_source()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        value.update_metadata(
            value.metadata,
            occurred_at=at(1),
        )


def test_rate_source_rejects_backdated_change() -> None:
    value = rate_source().activate(
        occurred_at=at(2),
        reason="approved",
    )

    with pytest.raises(
        ValueError,
        match="must not be earlier than updated_at",
    ):
        value.update_priority(
            5,
            occurred_at=at(1),
        )


def test_rate_source_allows_same_timestamp_change() -> None:
    value = rate_source().activate(
        occurred_at=at(1),
        reason="approved",
    )

    updated = value.update_priority(
        5,
        occurred_at=at(1),
    )

    assert updated.updated_at == at(1)
    assert updated.version == 3


def test_rate_source_update_chain_versions() -> None:
    value = rate_source()

    value = value.activate(
        occurred_at=at(1),
        reason="approved",
    )
    assert value.version == 2

    value = value.update_priority(
        5,
        occurred_at=at(2),
    )
    assert value.version == 3

    value = value.update_supported_currency_pairs(
        (
            "AUD/USD",
            "AUD/NZD",
        ),
        occurred_at=at(3),
    )
    assert value.version == 4

    value = value.update_freshness_policy(
        maximum_staleness_seconds=120,
        expected_latency_ms=250,
        expected_reliability=Decimal("0.999"),
        occurred_at=at(4),
    )
    assert value.version == 5

    value = value.update_trust_level(
        "trusted",
        occurred_at=at(5),
    )
    assert value.version == 6

    value = value.update_metadata(
        {
            "reviewed": True,
        },
        occurred_at=at(6),
    )
    assert value.version == 7


@pytest.mark.parametrize(
    "factory",
    [
        provider,
        rate_source,
    ],
)
def test_lifecycle_reason_is_required(
    factory: object,
) -> None:
    value = factory()  # type: ignore[operator]

    with pytest.raises(ValueError):
        value.activate(
            occurred_at=at(1),
            reason=" ",
        )


@pytest.mark.parametrize(
    "factory",
    [
        provider,
        rate_source,
    ],
)
def test_lifecycle_rejects_naive_timestamp(
    factory: object,
) -> None:
    value = factory()  # type: ignore[operator]

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        value.activate(
            occurred_at=datetime(
                2026,
                8,
                3,
                0,
                1,
            ),
            reason="approved",
        )


def test_lifecycle_domain_contains_no_runtime_authority() -> None:
    values = (
        provider(),
        rate_source(),
    )

    for value in values:
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


def test_lifecycle_preserves_exact_identifiers() -> None:
    provider_value = provider().activate(
        occurred_at=at(1),
        reason="approved",
    )

    source_value = rate_source().activate(
        occurred_at=at(1),
        reason="approved",
    )

    assert provider_value.provider_id == (
        ExchangeRateProviderId("provider-rba")
    )
    assert source_value.rate_source_id == (
        RateSourceId("source-rba-reference")
    )
    assert source_value.provider_id == (
        ExchangeRateProviderId("provider-rba")
    )
