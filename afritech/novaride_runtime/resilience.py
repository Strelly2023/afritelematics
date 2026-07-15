"""Production-hardening primitives for NovaRide resilience."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from time import monotonic
from typing import Any, Awaitable, Callable, Protocol

import httpx

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.events.hashing import canonical_hash
from afritech.novaride_runtime.models import (
    CircuitBreakerState,
    DegradedMode,
    FailoverEvent,
    FailoverState,
    ProviderHealth,
    ProviderHealthRecord,
    ProviderRoute,
    ProviderRouteDecision,
    ProviderState,
    RuntimeContext,
)


class ProviderProbe(Protocol):
    provider_name: str
    capability: str

    async def probe(self) -> ProviderHealth: ...


@dataclass(slots=True)
class HttpProviderProbe:
    provider_name: str
    capability: str
    health_url: str
    timeout_seconds: float = 2.0
    transport: httpx.AsyncBaseTransport | None = None

    async def probe(self) -> ProviderHealth:
        started = monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.get(self.health_url)
            latency_ms = int((monotonic() - started) * 1000)
            state = ProviderState.HEALTHY if response.status_code < 500 else ProviderState.DEGRADED
            return ProviderHealth(
                provider=self.provider_name,
                capability=self.capability,
                state=state,
                latency_ms=latency_ms,
                error_rate=Decimal("0"),
            )
        except Exception:
            return ProviderHealth(
                provider=self.provider_name,
                capability=self.capability,
                state=ProviderState.UNAVAILABLE,
                latency_ms=int((monotonic() - started) * 1000),
                error_rate=Decimal("1"),
            )


@dataclass(slots=True)
class HealthAggregator:
    degraded_after_failures: int = 3
    unavailable_after_failures: int = 5
    recover_to_degraded_successes: int = 3
    recover_to_healthy_successes: int = 5

    def apply(self, previous: ProviderHealthRecord | None, measurement: ProviderHealth, context: RuntimeContext) -> ProviderHealthRecord:
        now = utc_now()
        old_state = previous.state if previous else ProviderState.HEALTHY
        failures = previous.consecutive_failures if previous else 0
        successes = previous.consecutive_successes if previous else 0
        if measurement.state == ProviderState.HEALTHY:
            successes += 1
            failures = 0
        else:
            failures += 1
            successes = 0

        state = old_state
        if old_state == ProviderState.HEALTHY and failures >= self.degraded_after_failures:
            state = ProviderState.DEGRADED
        if old_state == ProviderState.DEGRADED and failures >= self.unavailable_after_failures:
            state = ProviderState.UNAVAILABLE
        if old_state == ProviderState.UNAVAILABLE and successes >= self.recover_to_degraded_successes:
            state = ProviderState.DEGRADED
        if old_state == ProviderState.DEGRADED and successes >= self.recover_to_healthy_successes:
            state = ProviderState.HEALTHY

        return ProviderHealthRecord(
            id=f"provider_health_{context.region_code}_{measurement.capability}_{measurement.provider}",
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            provider=measurement.provider,
            capability=measurement.capability,
            state=state,
            latency_ms=measurement.latency_ms,
            error_rate=measurement.error_rate,
            timeout_rate=Decimal("1") if measurement.state == ProviderState.UNAVAILABLE else Decimal("0"),
            success_rate=Decimal("1") if measurement.state == ProviderState.HEALTHY else Decimal("0"),
            consecutive_failures=failures,
            consecutive_successes=successes,
            last_successful_probe_at=now if measurement.state == ProviderState.HEALTHY else (previous.last_successful_probe_at if previous else None),
            last_state_transition_at=now if state != old_state else (previous.last_state_transition_at if previous else now),
        )


RETRY_POLICIES: dict[str, dict[str, float | int]] = {
    "provider_health": {"max_attempts": 3, "base_delay_seconds": 0.25, "max_delay_seconds": 2},
    "offline_sync": {"max_attempts": 8, "base_delay_seconds": 1, "max_delay_seconds": 300},
    "notification": {"max_attempts": 5, "base_delay_seconds": 2, "max_delay_seconds": 120},
}

NON_AUTOMATIC_RETRY_OPERATIONS = {
    "payment_capture",
    "refund",
    "ride_completion",
    "driver_payout",
    "ledger_posting",
    "emergency_escalation",
}


def retry_delay_seconds(policy_name: str, attempt: int, *, jitter: float | None = None) -> float:
    policy = RETRY_POLICIES[policy_name]
    base = float(policy["base_delay_seconds"])
    max_delay = float(policy["max_delay_seconds"])
    return min(max_delay, base * (2**attempt)) + (random.uniform(0, base) if jitter is None else jitter)


@dataclass(slots=True)
class CircuitBreaker:
    name: str
    failure_threshold: int
    open_duration_seconds: int
    half_open_max_calls: int
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failures: int = 0
    half_open_calls: int = 0
    opened_at_monotonic: float | None = None
    open_total: int = 0

    def allow_request(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            if self.opened_at_monotonic is not None and monotonic() - self.opened_at_monotonic >= self.open_duration_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
            else:
                return False
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                return False
            self.half_open_calls += 1
            return True
        return False

    def record_success(self) -> None:
        self.failures = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.opened_at_monotonic = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold or self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.opened_at_monotonic = monotonic()
            self.open_total += 1


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    provider: str
    capability: str
    health: ProviderState
    latency_ms: int
    error_rate: Decimal
    licensed_regions: tuple[str, ...]
    currencies: tuple[str, ...] = ()
    cost_rank: int = 100
    circuit_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    data_residency: str = "regional_or_approved_cross_border"


@dataclass(slots=True)
class PolicyProviderRouter:
    def select(
        self,
        context: RuntimeContext,
        *,
        capability: str,
        candidates: tuple[ProviderCandidate, ...],
        currency: str | None = None,
    ) -> tuple[ProviderRoute, ProviderRouteDecision]:
        attempted = tuple(candidate.provider for candidate in candidates)
        eligible = [
            candidate
            for candidate in candidates
            if candidate.capability == capability
            and context.region_code in candidate.licensed_regions
            and (currency is None or not candidate.currencies or currency in candidate.currencies)
            and candidate.circuit_state != CircuitBreakerState.OPEN
        ]
        eligible.sort(key=lambda item: (item.health != ProviderState.HEALTHY, item.error_rate, item.latency_ms, item.cost_rank))
        selected = eligible[0] if eligible else None
        degraded = DegradedMode.NORMAL if selected and selected.health == ProviderState.HEALTHY else DegradedMode.DEGRADED if selected else DegradedMode.OFFLINE
        reason = "healthy_lowest_latency_supported_corridor" if selected else "no_eligible_provider"
        route = ProviderRoute(
            capability=capability,
            selected_provider=selected.provider if selected else None,
            attempted_providers=attempted,
            degraded_mode=degraded,
            fallback_reason=None if selected and candidates and selected.provider == candidates[0].provider else "policy_fallback_selected",
        )
        evidence_payload = {
            "capability": capability,
            "region": context.region_code,
            "currency": currency,
            "attempted": attempted,
            "selected": route.selected_provider,
            "reason": reason,
        }
        decision = ProviderRouteDecision(
            id=f"route_{context.correlation_id}_{capability}_{route.selected_provider or 'none'}",
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            capability=capability,
            selected_provider=route.selected_provider,
            attempted_providers=attempted,
            degraded_mode=degraded,
            reason=reason,
            evidence_hash=canonical_hash(evidence_payload),
        )
        return route, decision


def prometheus_resilience_metrics(snapshot: dict[str, Any]) -> str:
    lines = [
        "# HELP novaride_offline_queue_depth Number of queued offline operations.",
        "# TYPE novaride_offline_queue_depth gauge",
        f"novaride_offline_queue_depth {snapshot.get('offline_queue_depth', 0)}",
        "# HELP novaride_provider_fallback_total Provider fallback decisions.",
        "# TYPE novaride_provider_fallback_total counter",
        f"novaride_provider_fallback_total {snapshot.get('provider_fallback_total', 0)}",
        "# HELP novaride_resilience_evidence_total Resilience evidence records.",
        "# TYPE novaride_resilience_evidence_total counter",
        f"novaride_resilience_evidence_total {snapshot.get('resilience_evidence_total', 0)}",
        "# HELP novaride_emergency_path_available Emergency path availability.",
        "# TYPE novaride_emergency_path_available gauge",
        f"novaride_emergency_path_available {snapshot.get('emergency_path_available', 1)}",
        "# HELP novaride_region_degraded_mode Regional degraded mode.",
        "# TYPE novaride_region_degraded_mode gauge",
        f"novaride_region_degraded_mode {snapshot.get('region_degraded_mode', 0)}",
    ]
    return "\n".join(lines) + "\n"


@dataclass(slots=True)
class FailoverController:
    current_state: FailoverState = FailoverState.NORMAL
    events: list[FailoverEvent] = field(default_factory=list)

    def evaluate(
        self,
        context: RuntimeContext,
        *,
        zone_healthy: bool,
        database_healthy: bool,
        message_stream_healthy: bool,
        emergency_path_healthy: bool,
        approval_reference: str | None = None,
    ) -> FailoverEvent | None:
        target = self.current_state
        automatic = True
        reason = "all_systems_nominal"
        if not emergency_path_healthy:
            target = FailoverState.EMERGENCY_ONLY
            reason = "emergency_path_unhealthy"
            automatic = approval_reference is None
        elif not database_healthy:
            target = FailoverState.REGION_DEGRADED
            reason = "database_unhealthy"
            automatic = False
        elif not zone_healthy:
            target = FailoverState.ZONE_FAILOVER
            reason = "zone_unhealthy"
        elif not message_stream_healthy:
            target = FailoverState.ZONE_DEGRADED
            reason = "message_stream_unhealthy"

        if target == self.current_state:
            return None
        if target in {FailoverState.REGION_DEGRADED, FailoverState.REGION_ISOLATED} and not approval_reference:
            raise AuthorityDenied("failover_policy_approval_required")
        event_payload = {
            "previous_state": self.current_state.value,
            "target_state": target.value,
            "reason": reason,
            "automatic": automatic,
            "approval_reference": approval_reference,
        }
        event = FailoverEvent(
            id=f"failover_{context.correlation_id}_{target.value.lower()}",
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            previous_state=self.current_state,
            target_state=target,
            reason=reason,
            automatic=automatic,
            approval_reference=approval_reference,
            evidence_hash=canonical_hash(event_payload),
        )
        self.current_state = target
        self.events.append(event)
        return event


async def run_with_retry(policy_name: str, operation: Callable[[], Awaitable[Any]]) -> Any:
    max_attempts = int(RETRY_POLICIES[policy_name]["max_attempts"])
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as exc:  # pragma: no cover - exercised by focused tests through final exception
            last_error = exc
            if attempt == max_attempts - 1:
                break
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_operation_not_attempted")


def next_retry_at(policy_name: str, attempt: int) -> Any:
    return utc_now() + timedelta(seconds=retry_delay_seconds(policy_name, attempt, jitter=0))
