from __future__ import annotations

import asyncio
import pytest
import httpx

from decimal import Decimal

from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.models import ActorType, CircuitBreakerState, FailoverState, ProviderHealth, ProviderState, RuntimeContext
from afritech.novaride_runtime.resilience import (
    CircuitBreaker,
    FailoverController,
    HealthAggregator,
    HttpProviderProbe,
    PolicyProviderRouter,
    ProviderCandidate,
    prometheus_resilience_metrics,
    retry_delay_seconds,
)


def _ctx() -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant_hardening",
        organization_id="org_hardening",
        region_code="KE",
        actor_type=ActorType.SYSTEM,
        actor_id="system",
        correlation_id="corr_hardening",
    )


def test_http_provider_probe_maps_status_and_failures() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    degraded = asyncio.run(HttpProviderProbe("maps_primary", "maps", "https://maps.example/health", transport=transport).probe())
    assert degraded.state == ProviderState.DEGRADED

    failing_transport = httpx.MockTransport(lambda request: (_ for _ in ()).throw(httpx.ConnectError("down", request=request)))
    unavailable = asyncio.run(HttpProviderProbe("sms", "sms", "https://sms.example/health", transport=failing_transport).probe())
    assert unavailable.state == ProviderState.UNAVAILABLE
    assert unavailable.error_rate == Decimal("1")


def test_health_aggregation_uses_hysteresis() -> None:
    aggregator = HealthAggregator()
    ctx = _ctx()
    record = None

    for _ in range(2):
        record = aggregator.apply(record, ProviderHealth("p", "maps", ProviderState.UNAVAILABLE), ctx)
        assert record.state == ProviderState.HEALTHY

    record = aggregator.apply(record, ProviderHealth("p", "maps", ProviderState.UNAVAILABLE), ctx)
    assert record.state == ProviderState.DEGRADED


def test_retry_delay_and_circuit_breaker_state_machine() -> None:
    assert retry_delay_seconds("offline_sync", 3, jitter=0) == 8

    breaker = CircuitBreaker("payment:primary", failure_threshold=2, open_duration_seconds=60, half_open_max_calls=1)
    assert breaker.allow_request() is True
    breaker.record_failure()
    assert breaker.state == CircuitBreakerState.CLOSED
    breaker.record_failure()
    assert breaker.state == CircuitBreakerState.OPEN
    assert breaker.allow_request() is False


def test_policy_provider_router_prefers_eligible_low_latency_healthy_provider() -> None:
    ctx = _ctx()
    route, decision = PolicyProviderRouter().select(
        ctx,
        capability="mobile_money",
        currency="KES",
        candidates=(
            ProviderCandidate("M-Pesa", "mobile_money", ProviderState.HEALTHY, 210, Decimal("0"), ("KE",), ("KES",), 2),
            ProviderCandidate("Airtel Money", "mobile_money", ProviderState.HEALTHY, 165, Decimal("0"), ("KE",), ("KES",), 1),
            ProviderCandidate("Onafriq", "mobile_money", ProviderState.DEGRADED, 690, Decimal("0.2"), ("KE",), ("KES",), 3),
        ),
    )

    assert route.selected_provider == "Airtel Money"
    assert decision.evidence_hash.startswith("sha256:")
    assert decision.reason == "healthy_lowest_latency_supported_corridor"


def test_failover_controller_requires_approval_for_database_regional_degradation() -> None:
    ctx = _ctx()
    controller = FailoverController()

    with pytest.raises(AuthorityDenied):
        controller.evaluate(
            ctx,
            zone_healthy=True,
            database_healthy=False,
            message_stream_healthy=True,
            emergency_path_healthy=True,
        )

    event = controller.evaluate(
        ctx,
        zone_healthy=True,
        database_healthy=False,
        message_stream_healthy=True,
        emergency_path_healthy=True,
        approval_reference="approval_1",
    )
    assert event is not None
    assert event.target_state == FailoverState.REGION_DEGRADED
    assert event.evidence_hash.startswith("sha256:")


def test_prometheus_resilience_metrics_exports_required_names() -> None:
    metrics = prometheus_resilience_metrics(
        {
            "offline_queue_depth": 42,
            "provider_fallback_total": 3,
            "resilience_evidence_total": 7,
            "emergency_path_available": 1,
            "region_degraded_mode": 0,
        }
    )

    assert "novaride_offline_queue_depth 42" in metrics
    assert "novaride_provider_fallback_total 3" in metrics
    assert "novaride_emergency_path_available 1" in metrics
