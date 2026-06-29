"""NovaRide Phase 5 autonomous strategy engine.

This layer remains projection-only. It synthesizes demand, autonomy, pricing,
and profit signals into a bounded strategy surface for operators and planning
dashboards without mutating execution state.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase2 import build_phase2_status
from afritech.afriprogramming.phase3 import build_business_pricing_projection, build_phase3_status
from afritech.afriprogramming.phase4 import (
    build_business_budget_allocation_projection,
    build_business_profit_optimization_projection,
    build_phase4_status,
)


PHASE5_TOPIC = "novaride.phase5.autonomous_strategy_engine"
_SECURITY_KEYWORDS = {
    "fraud": ("fraud", "forgery", "tamper", "unauthorized", "suspicious", "replay"),
    "anomaly": ("anomaly", "delay", "skew", "drift", "deviation", "custody_gap"),
    "sos": ("sos", "emergency", "incident", "distress"),
    "blacklist": ("blacklist", "block", "ban", "suspend", "deny"),
}


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


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - defensive
        return Decimal(default)


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _text_blob(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (dict, list, tuple, set)):
            parts.append(str(value).lower())
        else:
            parts.append(str(value).lower())
    return " ".join(parts)


def _contains_keywords(value: Any, keywords: tuple[str, ...]) -> bool:
    blob = _text_blob(value)
    return any(keyword in blob for keyword in keywords)


def _ride_event_blob(event: dict[str, Any]) -> str:
    return _text_blob(
        event.get("event_type"),
        event.get("target"),
        event.get("status"),
        event.get("payload"),
    )


def _participant_rating_score(
    *,
    completion_rate: float,
    trust_score: float,
    anomaly_rate: float,
    fraud_rate: float,
    sos_rate: float,
) -> float:
    composite = (
        (completion_rate * 2.1)
        + ((trust_score / 100.0) * 1.6)
        - (anomaly_rate * 0.9)
        - (fraud_rate * 1.2)
        - (sos_rate * 0.7)
    )
    return round(_clamp(1.0 + composite, minimum=1.0, maximum=5.0), 2)


def _participant_trust_score(
    *,
    completion_rate: float,
    base_trust_score: float,
    anomaly_rate: float,
    fraud_rate: float,
    sos_rate: float,
    blacklist_hit: bool,
) -> int:
    score = (
        (completion_rate * 34.0)
        + (base_trust_score * 0.45)
        + ((1.0 - anomaly_rate) * 12.0)
        + ((1.0 - fraud_rate) * 8.0)
        + ((1.0 - sos_rate) * 6.0)
    )
    if blacklist_hit:
        score -= 22.0
    return int(round(_clamp(score, minimum=0.0, maximum=100.0)))


def _participant_status(*, trust_score: int, fraud_events: int, sos_events: int, blacklist_hit: bool) -> str:
    if blacklist_hit:
        return "blocked"
    if fraud_events > 0 or sos_events > 0 or trust_score < 70:
        return "watch"
    return "trusted"


def _participant_summary(
    *,
    subject_id: str,
    rides: list[dict[str, Any]],
    audit_events: list[dict[str, Any]],
    presence_by_driver: dict[str, dict[str, Any]],
    latest_org_trust: int,
    role: str,
) -> dict[str, Any]:
    total_rides = len(rides)
    completed_rides = sum(1 for ride in rides if ride.get("status") == "completed")
    cancelled_rides = sum(1 for ride in rides if ride.get("status") == "cancelled")
    active_rides = sum(1 for ride in rides if ride.get("status") in {"requested", "matched", "arriving", "in_progress"})
    ride_ids = {str(ride.get("ride_id")) for ride in rides}
    target_events = [
        event
        for event in audit_events
        if str(event.get("target")) in ride_ids or str(event.get("target")) == subject_id
    ]
    fraud_events = [event for event in target_events if _contains_keywords(_ride_event_blob(event), _SECURITY_KEYWORDS["fraud"])]
    anomaly_events = [event for event in target_events if _contains_keywords(_ride_event_blob(event), _SECURITY_KEYWORDS["anomaly"])]
    sos_events = [event for event in target_events if _contains_keywords(_ride_event_blob(event), _SECURITY_KEYWORDS["sos"])]
    blacklist_events = [event for event in target_events if _contains_keywords(_ride_event_blob(event), _SECURITY_KEYWORDS["blacklist"])]
    completion_rate = round(completed_rides / total_rides, 6) if total_rides else 0.0
    anomaly_rate = round(len(anomaly_events) / total_rides, 6) if total_rides else 0.0
    fraud_rate = round(len(fraud_events) / total_rides, 6) if total_rides else 0.0
    sos_rate = round(len(sos_events) / total_rides, 6) if total_rides else 0.0
    if role == "driver":
        base_trust = float(presence_by_driver.get(subject_id, {}).get("trust_score", latest_org_trust) or latest_org_trust)
    else:
        base_trust = float(latest_org_trust)
    trust_score = _participant_trust_score(
        completion_rate=completion_rate,
        base_trust_score=base_trust,
        anomaly_rate=anomaly_rate,
        fraud_rate=fraud_rate,
        sos_rate=sos_rate,
        blacklist_hit=bool(blacklist_events),
    )
    rating_score = _participant_rating_score(
        completion_rate=completion_rate,
        trust_score=float(trust_score),
        anomaly_rate=anomaly_rate,
        fraud_rate=fraud_rate,
        sos_rate=sos_rate,
    )
    return {
        "subject_id": subject_id,
        "role": role,
        "status": _participant_status(
            trust_score=trust_score,
            fraud_events=len(fraud_events),
            sos_events=len(sos_events),
            blacklist_hit=bool(blacklist_events),
        ),
        "rating_score": rating_score,
        "trust_score": trust_score,
        "completion_rate": round(completion_rate, 6),
        "completed_rides": completed_rides,
        "cancelled_rides": cancelled_rides,
        "active_rides": active_rides,
        "anomaly_events": len(anomaly_events),
        "fraud_events": len(fraud_events),
        "sos_events": len(sos_events),
        "blacklist_hit": bool(blacklist_events),
        "base_trust_score": round(base_trust, 2),
        "source": "computed_operational_signals_v1",
    }


def build_trust_safety_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    rides = _store().list_rides(organization_id=organization_id, limit=limit)
    driver_presence = _store().list_driver_presence(organization_id=organization_id, limit=limit)
    audit_events = _store().list_audit_events(organization_id=organization_id, limit=limit)
    trust_scores = _store().list_trust_scores(organization_id=organization_id, limit=limit)
    zero_trust_policies = _store().list_zero_trust_policies(organization_id=organization_id, limit=limit)
    zero_trust_decisions = _store().list_zero_trust_decisions(organization_id=organization_id, limit=limit)
    notifications = _store().list_notifications(organization_id=organization_id, limit=limit)
    autonomy = build_control_projection("build_dashboard_autonomy", organization_id=organization_id, limit=limit)

    latest_org_trust = int(trust_scores[0]["trust_score"]) if trust_scores else 92
    presence_by_driver = {
        str(item["driver_id"]): item
        for item in driver_presence
        if item.get("driver_id") is not None
    }

    rides_by_driver: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rides_by_passenger: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ride in rides:
        driver_id = ride.get("driver_id")
        passenger_id = ride.get("passenger_id")
        if driver_id:
            rides_by_driver[str(driver_id)].append(ride)
        if passenger_id:
            rides_by_passenger[str(passenger_id)].append(ride)

    driver_ratings = [
        _participant_summary(
            subject_id=driver_id,
            rides=subject_rides,
            audit_events=audit_events,
            presence_by_driver=presence_by_driver,
            latest_org_trust=latest_org_trust,
            role="driver",
        )
        for driver_id, subject_rides in rides_by_driver.items()
    ]
    rider_ratings = [
        _participant_summary(
            subject_id=passenger_id,
            rides=subject_rides,
            audit_events=audit_events,
            presence_by_driver=presence_by_driver,
            latest_org_trust=latest_org_trust,
            role="rider",
        )
        for passenger_id, subject_rides in rides_by_passenger.items()
    ]
    driver_ratings.sort(key=lambda item: (item["trust_score"], item["rating_score"], item["completed_rides"]), reverse=True)
    rider_ratings.sort(key=lambda item: (item["trust_score"], item["rating_score"], item["completed_rides"]), reverse=True)

    fraud_alerts: list[dict[str, Any]] = []
    anomaly_alerts: list[dict[str, Any]] = []
    sos_events: list[dict[str, Any]] = []
    for event in audit_events:
        blob = _ride_event_blob(event)
        if _contains_keywords(blob, _SECURITY_KEYWORDS["fraud"]):
            fraud_alerts.append(
                {
                    "event_id": event.get("event_id"),
                    "event_type": event.get("event_type"),
                    "target": event.get("target"),
                    "status": event.get("status"),
                    "created_at": event.get("created_at"),
                    "summary": "Fraud-related signal detected in the audit trail.",
                }
            )
        if _contains_keywords(blob, _SECURITY_KEYWORDS["anomaly"]):
            anomaly_alerts.append(
                {
                    "event_id": event.get("event_id"),
                    "event_type": event.get("event_type"),
                    "target": event.get("target"),
                    "status": event.get("status"),
                    "created_at": event.get("created_at"),
                    "summary": "Trip anomaly detected from replay or operational telemetry.",
                }
            )
        if _contains_keywords(blob, _SECURITY_KEYWORDS["sos"]):
            sos_events.append(
                {
                    "event_id": event.get("event_id"),
                    "event_type": event.get("event_type"),
                    "target": event.get("target"),
                    "status": event.get("status"),
                    "created_at": event.get("created_at"),
                    "summary": "SOS or emergency escalation detected.",
                }
            )

    blocked_subjects: list[dict[str, Any]] = []
    for decision in zero_trust_decisions:
        decision_blob = _text_blob(
            decision.get("action"),
            decision.get("resource"),
            decision.get("reason"),
            decision.get("subject"),
        )
        if bool(decision.get("allowed")):
            continue
        if _contains_keywords(decision_blob, _SECURITY_KEYWORDS["blacklist"]) or "deny" in decision_blob:
            blocked_subjects.append(
                {
                    "decision_id": decision.get("decision_id"),
                    "subject": decision.get("subject"),
                    "action": decision.get("action"),
                    "resource": decision.get("resource"),
                    "reason": decision.get("reason"),
                    "created_at": decision.get("created_at"),
                }
            )

    total_rides = len(rides)
    completed_rides = sum(1 for ride in rides if ride.get("status") == "completed")
    cancelled_rides = sum(1 for ride in rides if ride.get("status") == "cancelled")
    completion_rate = round(completed_rides / total_rides, 6) if total_rides else 0.0
    cancellation_rate = round(cancelled_rides / total_rides, 6) if total_rides else 0.0
    total_fraud = len(fraud_alerts)
    total_anomalies = len(anomaly_alerts)
    total_sos = len(sos_events)
    latest_trust_readout = trust_scores[0] if trust_scores else None
    driver_trust_average = (
        round(sum(item["trust_score"] for item in driver_ratings) / len(driver_ratings), 2)
        if driver_ratings
        else float(latest_org_trust)
    )
    rider_trust_average = (
        round(sum(item["trust_score"] for item in rider_ratings) / len(rider_ratings), 2)
        if rider_ratings
        else float(latest_org_trust)
    )
    trust_score = int(
        round(
            _clamp(
                (driver_trust_average * 0.44)
                + (rider_trust_average * 0.28)
                + (latest_org_trust * 0.18)
                + ((1.0 - min(1.0, cancellation_rate)) * 10.0),
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    fraud_score = int(round(_clamp((total_fraud * 28.0) + (total_anomalies * 10.0), minimum=0.0, maximum=100.0)))
    anomaly_score = int(round(_clamp((total_anomalies * 25.0) + (total_sos * 12.0), minimum=0.0, maximum=100.0)))
    safety_score = int(
        round(
            _clamp(
                trust_score - fraud_score * 0.35 - anomaly_score * 0.25 - (len(blocked_subjects) * 5.0),
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    status = "safe" if safety_score >= 90 and total_fraud == 0 and total_sos == 0 else "watch" if safety_score >= 70 else "hold"

    safe_to_autorun = bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False))
    autonomy_thresholds = dict(autonomy.get("autonomy", {}).get("thresholds", {}))
    safe_limit_rules = {
        "projection_only": True,
        "read_only": True,
        "tenant_isolation_preserved": True,
        "no_payment_authority": True,
        "no_provider_direct_access": True,
        "no_dispatch_override": True,
        "min_driver_trust_score": 85,
        "min_rider_trust_score": 80,
        "max_fraud_events": 0,
        "max_anomaly_events": 1,
        "max_open_sos_incidents": 0,
        "max_blacklist_entries": 0,
        "operator_confirmation_required": not safe_to_autorun,
        "autonomy_thresholds": autonomy_thresholds,
    }
    bridge_mode = "bounded_autonomous" if safe_to_autorun and status == "safe" and not blocked_subjects else "supervised" if safety_score >= 75 else "held"
    auto_execution_bridge = {
        "mode": bridge_mode,
        "safe_to_autorun": bool(safe_to_autorun and status == "safe" and not blocked_subjects),
        "safe_limit_rules": safe_limit_rules,
        "recommendations": [
            "keep execution read-only outside the platform authority boundary",
            "require operator confirmation when fraud, anomaly, or SOS signals are present",
            "allow only bounded reranking, never payment or provider mutation",
        ],
        "bounded_actions": [
            "re-rank drivers by trust score only",
            "surface blacklist and SOS signals to the operator console",
            "hold any autonomous execution until all safe limits are satisfied",
        ],
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }

    overall_ratings = {
        "drivers": driver_ratings,
        "riders": rider_ratings,
        "summary": {
            "driver_count": len(driver_ratings),
            "rider_count": len(rider_ratings),
            "driver_average_rating": round(
                sum(item["rating_score"] for item in driver_ratings) / len(driver_ratings), 2
            ) if driver_ratings else 0.0,
            "rider_average_rating": round(
                sum(item["rating_score"] for item in rider_ratings) / len(rider_ratings), 2
            ) if rider_ratings else 0.0,
            "driver_average_trust": round(driver_trust_average, 2),
            "rider_average_trust": round(rider_trust_average, 2),
            "completion_rate": round(completion_rate, 6),
            "cancellation_rate": round(cancellation_rate, 6),
            "source": "computed_operational_signals_v1",
        },
    }
    trust = {
        "organization_trust_score": latest_org_trust,
        "overall_trust_score": trust_score,
        "driver_trust_score": int(round(driver_trust_average)),
        "rider_trust_score": int(round(rider_trust_average)),
        "fraud_score": fraud_score,
        "anomaly_score": anomaly_score,
        "safety_score": safety_score,
        "status": status,
        "latest_trust_record": latest_trust_readout,
    }
    return {
        "view": "novaride_phase5_trust_safety",
        "phase": "5",
        "platform": "NovaRide Phase 5",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "ratings": overall_ratings,
        "trust": trust,
        "fraud_detection": {
            "alerts": fraud_alerts,
            "count": total_fraud,
            "risk_level": "high" if total_fraud >= 2 else "watch" if total_fraud == 1 else "clear",
            "status": "open" if total_fraud else "clear",
        },
        "trip_anomaly_detection": {
            "alerts": anomaly_alerts,
            "count": total_anomalies,
            "risk_level": "high" if total_anomalies >= 2 else "watch" if total_anomalies == 1 else "clear",
            "status": "open" if total_anomalies else "clear",
        },
        "sos": {
            "open_incidents": sos_events,
            "open_count": total_sos,
            "status": "active" if total_sos else "clear",
        },
        "blacklist": {
            "blocked_subjects": blocked_subjects,
            "count": len(blocked_subjects),
            "policy_count": len(zero_trust_policies),
            "source": "zero_trust_decisions",
        },
        "auto_execution_bridge": auto_execution_bridge,
        "guardrails": {
            "tenant_isolation_preserved": True,
            "active_subscription_required": True,
            "read_only": True,
            "projection_only": True,
            "no_runtime_mutation": True,
            "no_payment_authority": True,
            "no_provider_direct_access": True,
            "no_dispatch_override": True,
        },
        "notifications": {
            "count": len(notifications),
            "latest": notifications[:5],
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def _build_city_strategy_rows(organization_id: str, limit: int = 100) -> list[dict[str, Any]]:
    demand = build_control_projection("build_dashboard_demand_forecast", organization_id=organization_id, limit=limit)
    budget = build_business_budget_allocation_projection(organization_id=organization_id, limit=limit)
    pricing = build_business_pricing_projection(organization_id=organization_id, limit=limit)
    autonomy = build_control_projection("build_dashboard_autonomy", organization_id=organization_id, limit=limit)

    demand_rows = {row["city"]: row for row in demand.get("city_forecasts", [])}
    budget_rows = {row["city"]: row for row in budget.get("budget_allocation", {}).get("city_allocations", [])}
    top_zone = demand.get("realtime_analytics", {}).get("live_state", {}).get("zone") or _latest_zone(organization_id)
    pricing_posture = pricing.get("pricing", {}).get("pricing_posture", "balanced")
    price_multiplier = _safe_decimal(pricing.get("pricing", {}).get("price_multiplier", "1.00"))
    take_rate = _safe_decimal(pricing.get("incentives", {}).get("commercial_take_rate", "0.35"))
    safe_to_autorun = bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False))

    city_names = sorted(set(demand_rows) | set(budget_rows)) or [top_zone]
    rows: list[dict[str, Any]] = []
    for city in city_names:
        demand_row = dict(demand_rows.get(city, {}))
        budget_row = dict(budget_rows.get(city, {}))
        demand_index = float(demand_row.get("demand_index", 0.0))
        demand_level = str(demand_row.get("demand_level") or "low")
        supply_gap = int(demand_row.get("supply_gap", budget_row.get("active_rides", 0) - budget_row.get("active_drivers", 0)))
        trust_score = int(budget_row.get("trust_score", demand_row.get("trust_score", 92)))
        coverage_score = int(budget_row.get("coverage_score", 0))
        projected_profit = _safe_decimal(budget_row.get("projected_profit", "0.00"))
        projected_margin = _safe_decimal(budget_row.get("projected_margin", "0.00"))
        recommended_budget = _safe_decimal(budget_row.get("recommended_budget", "0.00"))
        score = (
            Decimal(str(demand_index)) * Decimal("0.45")
            + (projected_margin * Decimal("100.0")) * Decimal("0.25")
            + Decimal(str(trust_score)) * Decimal("0.15")
            + Decimal(str(coverage_score)) * Decimal("0.10")
            + Decimal(str(max(0, 12 - supply_gap * 2)))
        )
        if demand_level == "high" and supply_gap > 0:
            strategy_lane = "supply_reposition"
            recommended_action = f"Shift supply toward {city}"
            strategy_reason = "Demand pressure exceeds available supply."
        elif projected_margin < Decimal("0.35"):
            strategy_lane = "margin_guard"
            recommended_action = f"Constrain spend in {city}"
            strategy_reason = "Projected margin is below target."
        elif demand_level == "moderate":
            strategy_lane = "balanced_growth"
            recommended_action = f"Hold balanced coverage near {city}"
            strategy_reason = "Demand is stable enough for controlled growth."
        else:
            strategy_lane = "monitor"
            recommended_action = f"Maintain watch around {city}"
            strategy_reason = "Current pressure does not justify reallocation."
        rows.append(
            {
                "city": city,
                "demand_level": demand_level,
                "demand_index": round(demand_index, 4),
                "supply_gap": supply_gap,
                "trust_score": trust_score,
                "coverage_score": coverage_score,
                "recommended_budget": _money_text(recommended_budget),
                "projected_profit": _money_text(projected_profit),
                "projected_margin": round(float(projected_margin), 4),
                "priority_score": round(float(score), 4),
                "strategy_lane": strategy_lane,
                "recommended_action": recommended_action,
                "strategy_reason": strategy_reason,
                "pricing_posture": pricing_posture,
                "price_multiplier": round(float(price_multiplier), 4),
                "commercial_take_rate": round(float(take_rate), 4),
                "autonomous_enabled": safe_to_autorun,
            }
        )

    return sorted(rows, key=lambda row: (row["priority_score"], row["demand_index"], row["city"]), reverse=True)


def build_autonomous_strategy_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    phase2_status = build_phase2_status(organization_id=organization_id, limit=limit)
    phase3_status = build_phase3_status(organization_id=organization_id, limit=limit)
    phase4_status = build_phase4_status(organization_id=organization_id, limit=limit)
    demand = build_control_projection("build_dashboard_demand_forecast", organization_id=organization_id, limit=limit)
    autonomy = build_control_projection("build_dashboard_autonomy", organization_id=organization_id, limit=limit)
    pricing = build_business_pricing_projection(organization_id=organization_id, limit=limit)
    budget = build_business_budget_allocation_projection(organization_id=organization_id, limit=limit)
    profit = build_business_profit_optimization_projection(organization_id=organization_id, limit=limit)

    city_strategy_rows = _build_city_strategy_rows(organization_id, limit=limit)
    top_city = city_strategy_rows[0] if city_strategy_rows else {
        "city": _latest_zone(organization_id),
        "strategy_lane": "monitor",
        "recommended_action": "Maintain watch",
        "strategy_reason": "No live city pressure is currently visible.",
        "priority_score": 0.0,
        "demand_level": "low",
        "demand_index": 0.0,
        "supply_gap": 0,
    }
    autonomous_enabled = bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False))
    strategy_mode = "autonomous" if autonomous_enabled and phase4_status.get("ready", False) else "supervised" if phase3_status.get("ready", False) else "advisory"
    recommendation = {
        "primary_city": top_city["city"],
        "strategy_lane": top_city["strategy_lane"],
        "action": top_city["recommended_action"],
        "reason": top_city["strategy_reason"],
        "next_step": "Review operator strategy panel and confirm bounded reallocation.",
    }
    strategy_windows = []
    for window in demand.get("forecast_windows", []):
        strategy_windows.append(
            {
                "horizon": window["horizon"],
                "expected_rides": window["expected_rides"],
                "expected_supply_gap": window["expected_supply_gap"],
                "recommended_action": window["recommended_action"],
            }
        )
    strategy = {
        "mode": strategy_mode,
        "primary_city": top_city["city"],
        "strategy_lane": top_city["strategy_lane"],
        "priority_score": top_city["priority_score"],
        "city_count": len(city_strategy_rows),
        "autonomous_enabled": autonomous_enabled,
        "bounded_autonomy": True,
        "planning_objective": "balance demand, supply, trust, and profit inside governed thresholds",
        "city_priorities": city_strategy_rows,
        "strategy_windows": strategy_windows,
        "recommendation": recommendation,
        "guardrails": {
            "tenant_isolation_preserved": True,
            "active_subscription_required": True,
            "read_only": True,
            "projection_only": True,
            "no_runtime_mutation": True,
            "no_payment_authority": True,
            "no_provider_direct_access": True,
            "no_dispatch_override": True,
        },
    }
    return {
        "view": "novaride_phase5_autonomous_strategy_engine",
        "phase": "5",
        "platform": "NovaRide Phase 5",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "model": {
            "name": "bounded_autonomous_strategy_engine",
            "version": "1.0.0",
            "mode": strategy_mode,
            "projection_only": True,
            "read_only": True,
        },
        "phase2": phase2_status,
        "phase3": phase3_status,
        "phase4": phase4_status,
        "autonomy": autonomy,
        "demand_forecast": demand,
        "pricing": pricing,
        "budget_allocation": budget,
        "profit_optimization": profit,
        "strategy": strategy,
        "readiness": {
            "phase4_ready": bool(phase4_status.get("ready", False)),
            "phase3_ready": bool(phase3_status.get("ready", False)),
            "phase2_ready": bool(phase2_status.get("ready", False)),
            "demand_forecast_ready": bool(demand.get("forecast_windows")),
            "autonomy_ready": bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False) or autonomy.get("autonomy", {}).get("mode")),
            "pricing_ready": bool(pricing.get("readiness", {}).get("pricing_verified", False)),
            "profit_optimization_ready": bool(profit.get("readiness", {}).get("budget_allocation_verified", False)),
            "strategy_verified": bool(city_strategy_rows) and strategy_mode in {"supervised", "autonomous", "advisory"},
            "tenant_isolation_preserved": True,
        },
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "decision_history": {
            "source": source or "afriride_operator_dashboard",
            "updated_at": _now(),
            "decision_chain": [
                "phase2_dispatch_autonomy",
                "phase3_business_pricing",
                "phase4_budget_optimization",
                "phase5_autonomous_strategy",
            ],
        },
    }


def build_phase5_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase2_status = build_phase2_status(organization_id=org_id, limit=limit)
    phase3_status = build_phase3_status(organization_id=org_id, limit=limit)
    phase4_status = build_phase4_status(organization_id=org_id, limit=limit)
    strategy = build_autonomous_strategy_projection(organization_id=org_id, limit=limit)
    trust_safety = build_trust_safety_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase4_ready": bool(phase4_status.get("ready", False)),
        "phase3_ready": bool(phase3_status.get("ready", False)),
        "phase2_ready": bool(phase2_status.get("ready", False)),
        "demand_forecast_ready": bool(strategy["demand_forecast"].get("forecast_windows")),
        "autonomy_ready": bool(strategy["autonomy"].get("autonomy", {}).get("safe_to_autorun", False) or strategy["autonomy"].get("autonomy", {}).get("mode")),
        "strategy_verified": bool(strategy["strategy"]["city_priorities"]),
        "tenant_isolation_preserved": bool(strategy["strategy"]["guardrails"]["tenant_isolation_preserved"]),
        "trust_safety_ready": bool(trust_safety.get("read_only", False)),
        "auto_execution_bridge_ready": bool(trust_safety.get("auto_execution_bridge", {}).get("projection_only", False)),
    }
    return {
        "view": "novaride_phase5_status",
        "phase": "5",
        "platform": "NovaRide Phase 5",
        "organization_id": org_id,
        "phase2": phase2_status,
        "phase3": phase3_status,
        "phase4": phase4_status,
        "strategy": strategy,
        "trust_safety": trust_safety,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE5_TOPIC",
    "build_autonomous_strategy_projection",
    "build_phase5_status",
    "build_trust_safety_projection",
]
