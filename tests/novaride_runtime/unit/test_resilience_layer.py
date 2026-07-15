from __future__ import annotations

from decimal import Decimal

from afritech.novaride_runtime.models import ActorType, DegradedMode, ProviderHealth, ProviderState, RuntimeContext
from afritech.novaride_runtime.services import create_runtime


def _ctx(actor_type: ActorType = ActorType.RIDER, actor_id: str = "rider_1") -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant_resilience",
        organization_id="org_resilience",
        region_code="KE",
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id="corr_resilience",
    )


def test_resilience_layer_queues_syncs_and_preserves_authoritative_boundaries() -> None:
    runtime = create_runtime()
    rider_ctx = _ctx()

    queued = runtime.resilience.queue_offline_operation(
        rider_ctx,
        operation_type="booking_request",
        payload={"pickup": "Westlands", "destination": "JKIA", "payment": "M-Pesa"},
        idempotency_key="offline-booking-1",
        authority_required=True,
    )

    assert queued.status == "QUEUED_AUTHORITY_REQUIRED"
    assert runtime.resilience.queue_offline_operation(
        rider_ctx,
        operation_type="booking_request",
        payload={"pickup": "Westlands", "destination": "JKIA", "payment": "M-Pesa"},
        idempotency_key="offline-booking-1",
        authority_required=True,
    ).id == queued.id

    sync = runtime.resilience.synchronize(rider_ctx)

    assert sync.queued == 1
    assert sync.synced == 0
    assert sync.awaiting_authority == 1
    assert sync.status == "PARTIAL_AUTHORITY_REQUIRED"

    conflict = runtime.resilience.resolve_conflict(domain="trip", local_version=3, server_version=4)
    assert conflict["winner"] == "server"
    assert conflict["policy"] == "server_authoritative_for_core_state"

    status = runtime.resilience.status("tenant_resilience")
    assert status["awaiting_authority"] == 1
    assert status["core_journey_preserved_under_degradation"] is True


def test_resilience_layer_routes_around_failed_providers_and_records_evidence() -> None:
    runtime = create_runtime()
    system_ctx = _ctx(ActorType.SYSTEM, "system")

    route = runtime.resilience.route_provider(
        system_ctx,
        capability="card_payment",
        providers=(
            ProviderHealth("primary_card", "card_payment", ProviderState.UNAVAILABLE, latency_ms=5000, error_rate=Decimal("1")),
            ProviderHealth("mobile_money", "card_payment", ProviderState.HEALTHY, latency_ms=180, error_rate=Decimal("0.01")),
        ),
    )

    assert route.selected_provider == "mobile_money"
    assert route.degraded_mode == DegradedMode.DEGRADED
    assert route.fallback_reason == "primary_provider_unhealthy"
    assert runtime.resilience.graceful_degradation("card_payment")["fallback"] == "offer_wallet_mobile_money_or_cash"

    command_center = runtime.read_models.command_center("tenant_resilience")
    assert command_center["resilience"]["resilience_evidence_records"] == 1
    assert {"ProviderRouteEvaluated", "ResilienceEvidenceRecorded"}.issubset(
        {event.event_type for event in runtime.repositories.events.all()}
    )
