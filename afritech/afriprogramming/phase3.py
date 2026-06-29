"""NovaRide Phase 3 business layer pricing and incentive projections.

This module keeps pricing and incentive logic deterministic, tenant-scoped,
and projection-only. It reads the existing ride, driver, and analytics state
and converts it into a governed business-layer surface for operators and
product teams.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase2 import build_phase2_status
from afritech.mobility.federation import FederatedParticipant
from afritech.mobility.market import (
    ALLOWED_INCENTIVES,
    MarketAllocation,
    MarketGovernanceError,
    MarketState,
    build_market_decision,
    evaluate_market_invariants,
    validate_market_decision,
)
from afritech.mobility.trust_network import TrustProfile


PHASE3_TOPIC = "novaride.phase3.business_pricing"


def _store():
    return get_phase_store()


def _now() -> str:
    return phase_now()


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _latest_zone(organization_id: str) -> str:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)
    return "CBD"


def _latest_trust_score(organization_id: str) -> int:
    trust = _store().latest_trust_score(organization_id=organization_id)
    if trust is not None:
        try:
            return int(trust.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        try:
            return int(snapshot.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    return 92


def _organization_subscription(organization_id: str) -> dict[str, Any] | None:
    return _store().latest_active_subscription(organization_id=organization_id)


def _base_price_for_organization(organization_id: str, rides: list[dict[str, Any]]) -> Decimal:
    values: list[Decimal] = []
    for ride in rides:
        raw = ride.get("fare_estimate") or ride.get("final_fare")
        if raw is None:
            continue
        try:
            values.append(Decimal(str(raw)))
        except Exception:  # pragma: no cover - defensive
            continue
    if values:
        return (sum(values) / Decimal(len(values))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            for key in ("base_fare", "average_fare", "avg_fare"):
                raw = payload.get(key)
                if raw is None:
                    continue
                try:
                    return Decimal(str(raw)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                except Exception:  # pragma: no cover - defensive
                    continue
    return Decimal("25.00")


def _currency_for_organization(organization_id: str, rides: list[dict[str, Any]]) -> str:
    counter: Counter[str] = Counter()
    for ride in rides:
        currency = str(ride.get("currency") or "").strip().upper()
        if currency:
            counter[currency] += 1
    if counter:
        return counter.most_common(1)[0][0]
    subscription = _organization_subscription(organization_id)
    if subscription and str(subscription.get("plan", "")).lower() == "enterprise":
        return "AUD"
    return "AUD"


def _active_driver_rows(organization_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in _store().list_driver_presence(organization_id=organization_id, limit=100)
        if str(row.get("status", "")).lower() in {"online", "busy"}
    ]


def _relevant_rides(organization_id: str) -> list[dict[str, Any]]:
    rides = _store().list_rides(organization_id=organization_id, limit=100)
    return [
        ride
        for ride in rides
        if str(ride.get("status", "")).lower() not in {"cancelled"}
    ]


def _trust_profile_for_driver(driver: dict[str, Any], *, organization_id: str, ride_count: int) -> TrustProfile:
    score = float(driver.get("trust_score") or 92.0)
    completed = max(0, ride_count - 1)
    return TrustProfile(
        participant_id=str(driver.get("driver_id") or driver.get("user_id") or f"driver-{organization_id}"),
        total_operations=max(1, ride_count),
        successful_operations=max(0, completed),
        anomaly_events=0,
        disputes=0,
        average_rating=min(5.0, max(3.5, score / 20.0)),
        trust_score=max(0.0, min(100.0, score)),
        last_updated=str(driver.get("updated_at") or driver.get("last_seen") or _now()),
        event_history=(),
        evidence_links=tuple(),
    )


def _fallback_participant(organization_id: str, trust_score: int) -> FederatedParticipant:
    profile = TrustProfile(
        participant_id=f"market-{organization_id}",
        total_operations=1,
        successful_operations=1,
        anomaly_events=0,
        disputes=0,
        average_rating=4.8,
        trust_score=float(trust_score),
        last_updated=_now(),
        event_history=(),
        evidence_links=tuple(),
    )
    return FederatedParticipant(
        participant_id=f"market-{organization_id}",
        home_network="novaride",
        roles=("market_reference",),
        trust_profile=profile,
        federation_status="verified",
        federation_weight=0.85,
        verification_level="verified",
        cross_network_events=0,
        evidence_links=tuple(),
        metadata=(("organization_id", organization_id), ("kind", "fallback_market_reference")),
    )


def _balancing_reference_participant(organization_id: str, trust_score: int) -> FederatedParticipant:
    profile = TrustProfile(
        participant_id=f"market-{organization_id}-balance",
        total_operations=1,
        successful_operations=1,
        anomaly_events=0,
        disputes=0,
        average_rating=4.7,
        trust_score=float(max(0, min(100, trust_score - 1))),
        last_updated=_now(),
        event_history=(),
        evidence_links=tuple(),
    )
    return FederatedParticipant(
        participant_id=f"market-{organization_id}-balance",
        home_network="novaride",
        roles=("market_reference", "balancer"),
        trust_profile=profile,
        federation_status="verified",
        federation_weight=0.8,
        verification_level="verified",
        cross_network_events=0,
        evidence_links=tuple(),
        metadata=(("organization_id", organization_id), ("kind", "balancing_reference")),
    )


def _build_market_state(organization_id: str, *, limit: int = 100) -> MarketState:
    active_rides = _relevant_rides(organization_id)
    drivers = _active_driver_rows(organization_id)
    trust_score = _latest_trust_score(organization_id)
    zone = _latest_zone(organization_id)
    base_price = _base_price_for_organization(organization_id, active_rides)
    currency = _currency_for_organization(organization_id, active_rides)
    ride_counts = Counter(
        str(ride.get("driver_id"))
        for ride in active_rides
        if ride.get("driver_id")
    )
    participants: list[FederatedParticipant] = []
    for driver in drivers[:limit]:
        driver_id = str(driver.get("driver_id") or driver.get("user_id") or "driver-unknown")
        participant = FederatedParticipant(
            participant_id=driver_id,
            home_network="novaride",
            roles=("driver", "mobility"),
            trust_profile=_trust_profile_for_driver(
                driver,
                organization_id=organization_id,
                ride_count=max(1, ride_counts.get(driver_id, 0)),
            ),
            federation_status="verified",
            federation_weight=0.85,
            verification_level="verified",
            cross_network_events=0,
            evidence_links=tuple(
                link
                for link in (
                    str(driver.get("busy_ride_id") or ""),
                    str(driver.get("last_seen") or ""),
                )
                if link.strip()
            ),
            metadata=(("organization_id", organization_id), ("status", driver.get("status", "online"))),
        )
        participants.append(participant)
    if not participants:
        participants.append(_fallback_participant(organization_id, trust_score))
    if len(participants) < 2:
        participants.append(_balancing_reference_participant(organization_id, trust_score))
    demand = max(1, len(active_rides) + 1)
    supply = max(0, len(drivers))
    return MarketState(
        market_id=f"novaride-business-{organization_id}",
        region_id=f"{organization_id}:{zone}",
        demand=demand,
        supply=supply,
        base_price=base_price,
        currency=currency,
        participants=tuple(participants),
        allocation_history=tuple(
            MarketAllocation(
                allocation_id=f"alloc-{organization_id}-{index}",
                participant_id=participant.participant_id,
                region_id=f"{organization_id}:{zone}",
                assignment_count=max(1, ride_counts.get(participant.participant_id, 0)),
                timestamp=index + 1,
                evidence_link=f"ride:{organization_id}:{participant.participant_id}",
                metadata=(("zone", zone), ("source", "phase3_business_layer")),
            )
            for index, participant in enumerate(participants)
            if ride_counts.get(participant.participant_id, 0) > 0
        ),
        active_incentives=tuple(),
        timestamp=limit,
        price_multiplier_hint=1.0 if demand == 0 else 1.1 if demand <= max(1, supply) else 1.35,
        price_floor=0.75,
        price_ceiling=2.5,
        max_allocation_share=0.35,
    )


def _pricing_posture(price_multiplier: float, demand: int, supply: int) -> str:
    if price_multiplier >= 1.5 or demand > supply + 2:
        return "surge_guarded"
    if price_multiplier >= 1.15:
        return "demand_rising"
    if price_multiplier <= 0.95:
        return "discounted"
    return "balanced"


def _incentive_focus(incentive_plan: tuple[str, ...]) -> str:
    if "allocation_rebalance_10%" in incentive_plan:
        return "network_balance"
    if "driver_bonus_20%" in incentive_plan or "driver_bonus_10%" in incentive_plan:
        return "driver_supply"
    if "availability_bonus_5%" in incentive_plan:
        return "availability"
    if "federation_balance_5%" in incentive_plan:
        return "federation_balance"
    return "neutral"


def build_business_pricing_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "novaride_business_portal",
) -> dict[str, Any]:
    state = _build_market_state(organization_id, limit=limit)
    decision = build_market_decision(state)
    invariant_report = evaluate_market_invariants(state, decision)
    validation_report = validate_market_decision(state, decision)
    active_subscription = _organization_subscription(organization_id)
    plan = str((active_subscription or {}).get("plan") or "free").lower()
    take_rate = {
        "free": 0.20,
        "basic": 0.18,
        "pro": 0.15,
        "enterprise": 0.12,
    }.get(plan, 0.20)
    platform_share = (decision.adjusted_price * Decimal(str(take_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    driver_pool = (decision.adjusted_price - platform_share).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    posture = _pricing_posture(decision.price_multiplier, state.demand, state.supply)
    focus = _incentive_focus(decision.incentive_plan)
    driver_message = (
        "High-demand driver incentives are active."
        if focus == "driver_supply"
        else "Allocation rebalance incentives are active."
        if focus == "network_balance"
        else "Supply coverage incentives are active."
        if focus == "availability"
        else "Pricing remains balanced."
    )
    rider_message = (
        "Visible fare pressure is present, but pricing remains deterministic."
        if posture in {"surge_guarded", "demand_rising"}
        else "Pricing is stable and transparent."
    )
    readiness = {
        "subscription_active": active_subscription is not None and str(active_subscription.get("status", "")).lower() == "active",
        "market_projection_ready": state.verified,
        "pricing_verified": validation_report.verified,
        "incentives_bounded": set(decision.incentive_plan).issubset(set(ALLOWED_INCENTIVES)),
        "tenant_isolation_preserved": all(
            participant.participant_id
            for participant in state.participants
        )
        and all(allocation.region_id.startswith(f"{organization_id}:") for allocation in state.allocation_history)
        and state.region_id.startswith(f"{organization_id}:"),
    }
    market_signals = {
        "demand": state.demand,
        "supply": state.supply,
        "zone": _latest_zone(organization_id),
        "trust_score": _latest_trust_score(organization_id),
        "active_drivers": len(_active_driver_rows(organization_id)),
        "active_rides": len(_relevant_rides(organization_id)),
    }
    return {
        "view": "novaride_phase3_business_pricing",
        "phase": "3",
        "organization_id": organization_id,
        "source": source or "novaride_business_portal",
        "market": state.canonical_dict(),
        "decision": decision.canonical_dict(),
        "invariant_report": invariant_report.canonical_dict(),
        "validation_report": validation_report.canonical_dict(),
        "pricing": {
            "base_price": _money_text(state.base_price),
            "price_multiplier": round(decision.price_multiplier, 6),
            "adjusted_price": _money_text(decision.adjusted_price),
            "currency": state.currency,
            "pricing_posture": posture,
            "price_band": "surge_guarded"
            if posture == "surge_guarded"
            else "demand_rising"
            if posture == "demand_rising"
            else "discounted"
            if posture == "discounted"
            else "balanced",
            "explanation": "Deterministic pricing is derived from demand, supply, trust, and bounded incentives.",
        },
        "incentives": {
            "plan": list(decision.incentive_plan),
            "focus": focus,
            "driver_message": driver_message,
            "rider_message": rider_message,
            "commercial_take_rate": round(take_rate, 4),
            "platform_share": _money_text(platform_share),
            "driver_pool": _money_text(driver_pool),
            "bounded": True,
        },
        "market_signals": market_signals,
        "controls": {
            "authority_boundary": state.authority_boundary,
            "projection_only": True,
            "read_only": True,
            "no_runtime_mutation": True,
            "no_provider_direct_access": True,
        },
        "readiness": readiness,
        "ready": all(readiness.values()),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_business_incentives_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "novaride_business_portal",
) -> dict[str, Any]:
    projection = build_business_pricing_projection(
        organization_id=organization_id,
        limit=limit,
        source=source,
    )
    projection["view"] = "novaride_phase3_business_incentives"
    return projection


def build_phase3_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase2_status = build_phase2_status(organization_id=org_id, limit=limit)
    pricing = build_business_pricing_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase2_ready": bool(phase2_status.get("ready", False)),
        "pricing_verified": bool(pricing["readiness"]["pricing_verified"]),
        "incentives_bounded": bool(pricing["readiness"]["incentives_bounded"]),
        "market_projection_ready": bool(pricing["readiness"]["market_projection_ready"]),
        "tenant_isolation_preserved": bool(pricing["readiness"]["tenant_isolation_preserved"]),
        "subscription_active": bool(pricing["readiness"]["subscription_active"]),
    }
    return {
        "view": "novaride_phase3_status",
        "phase": "3",
        "platform": "NovaRide Phase 3",
        "organization_id": org_id,
        "phase2": phase2_status,
        "pricing": pricing,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE3_TOPIC",
    "build_business_incentives_projection",
    "build_business_pricing_projection",
    "build_phase3_status",
]
