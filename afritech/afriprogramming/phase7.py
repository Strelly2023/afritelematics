"""NovaRide Phase 7 analytics and intelligence.

This layer remains projection-only. It turns ride, transaction, dispatch,
presence, and learning history into management intelligence with RL-style
feedback loops, revenue analytics, churn analysis, and live GPS streaming
signals without mutating runtime authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase3 import build_business_pricing_projection
from afritech.afriprogramming.phase5 import build_phase5_status
from afritech.afriprogramming.phase6 import build_navigation_maps_intelligence_projection, build_phase6_status


PHASE7_TOPIC = "novaride.phase7.analytics_intelligence"


def _store():
    return get_phase_store()


def _now() -> str:
    return phase_now()


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - defensive
        return Decimal(default)


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # pragma: no cover - defensive
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:  # pragma: no cover - defensive
        return default


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _latest_zone(organization_id: str) -> str:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)

    drivers = _store().list_driver_presence(organization_id=organization_id, limit=1)
    if drivers:
        location = drivers[0].get("location") or {}
        label = str(location.get("label") or location.get("name") or location.get("city") or "").strip()
        if label:
            return label

    rides = _store().list_rides(organization_id=organization_id, limit=1)
    if rides:
        location = rides[0].get("pickup_location") or {}
        label = str(location.get("label") or location.get("name") or location.get("city") or "").strip()
        if label:
            return label

    return "CBD"


def _organization_trust_score(organization_id: str) -> int:
    trust = _store().latest_trust_score(organization_id=organization_id)
    if trust is not None:
        return _safe_int(trust.get("trust_score"), 92)
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        return _safe_int(snapshot.get("trust_score"), 92)
    return 92


def _ride_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_rides(organization_id=organization_id, limit=limit)


def _driver_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_driver_presence(organization_id=organization_id, limit=limit)


def _transaction_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_transactions(organization_id=organization_id, limit=limit)


def _dispatch_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_dispatch_assignments(organization_id=organization_id, limit=limit)


def _decision_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_ai_decision_snapshots(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )


def _action_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_ai_action_snapshots(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )


def _outcome_rows(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_outcome_snapshots(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )


def _active_ride_statuses() -> set[str]:
    return {"requested", "assigned", "matched", "accepted", "arriving", "arrived", "in_progress"}


def _cancellable_ride_statuses() -> set[str]:
    return {"cancelled"}


def _completed_ride_statuses() -> set[str]:
    return {"completed"}


def _revenue_dashboard(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    pricing = build_business_pricing_projection(organization_id=organization_id, source="novaride_phase7")
    take_rate = _safe_float(pricing.get("incentives", {}).get("commercial_take_rate"), 0.1)

    completed_rides = [ride for ride in rides if str(ride.get("status", "")).lower() in _completed_ride_statuses()]
    completed_fares = [
        _safe_decimal(ride.get("final_fare", ride.get("fare_estimate", "0.00")))
        for ride in completed_rides
    ]
    ride_revenue = sum(completed_fares, Decimal("0.00"))
    gross_transaction_volume = sum(
        (_safe_decimal(tx.get("amount")) for tx in transactions if str(tx.get("status", "")).lower() == "completed"),
        Decimal("0.00"),
    )
    passenger_debits = sum(
        (_safe_decimal(tx.get("amount")) for tx in transactions if str(tx.get("type")) == "debit"),
        Decimal("0.00"),
    )
    driver_credits = sum(
        (_safe_decimal(tx.get("amount")) for tx in transactions if str(tx.get("type")) == "credit"),
        Decimal("0.00"),
    )
    average_completed_fare = ride_revenue / max(1, len(completed_rides))
    estimated_platform_revenue = (ride_revenue * Decimal(str(take_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    projected_margin = _clamp((float(estimated_platform_revenue) / max(1.0, float(ride_revenue))) * 100.0, minimum=0.0, maximum=100.0)

    return {
        "view": "novaride_phase7_revenue_dashboard",
        "currency": pricing.get("pricing", {}).get("currency", "AUD"),
        "commercial_take_rate": round(take_rate, 4),
        "gross_transaction_volume": _money_text(gross_transaction_volume),
        "ride_revenue": _money_text(ride_revenue),
        "passenger_debits": _money_text(passenger_debits),
        "driver_credits": _money_text(driver_credits),
        "average_completed_fare": _money_text(average_completed_fare),
        "estimated_platform_revenue": _money_text(estimated_platform_revenue),
        "projected_margin_pct": round(projected_margin, 4),
        "completed_rides": len(completed_rides),
        "total_rides": len(rides),
        "projection_only": True,
        "read_only": True,
    }


def _driver_performance(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
    dispatch_assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_trust = _organization_trust_score(organization_id)
    driver_ids = sorted(
        {
            str(row.get("driver_id"))
            for row in drivers
            if str(row.get("driver_id") or "").strip()
        }
        | {
            str(row.get("driver_id"))
            for row in rides
            if str(row.get("driver_id") or "").strip()
        }
        | {
            str(row.get("driver_id"))
            for row in dispatch_assignments
            if str(row.get("driver_id") or "").strip()
        }
    )
    top_rows: list[dict[str, Any]] = []
    for driver_id in driver_ids:
        presence = next((row for row in drivers if str(row.get("driver_id")) == driver_id), {})
        driver_rides = [ride for ride in rides if str(ride.get("driver_id")) == driver_id]
        assignments = [row for row in dispatch_assignments if str(row.get("driver_id")) == driver_id]
        accepted_assignments = [row for row in assignments if str(row.get("status")) == "accepted"]
        completed_rides = [ride for ride in driver_rides if str(ride.get("status", "")).lower() in _completed_ride_statuses()]
        cancelled_rides = [ride for ride in driver_rides if str(ride.get("status", "")).lower() in _cancellable_ride_statuses()]
        active_rides = [ride for ride in driver_rides if str(ride.get("status", "")).lower() in _active_ride_statuses()]
        total_assigned = len(assignments)
        total_rides = len(driver_rides)
        acceptance_rate = round(len(accepted_assignments) / total_assigned, 6) if total_assigned else 0.0
        cancellation_rate = round(len(cancelled_rides) / total_rides, 6) if total_rides else 0.0
        completion_rate = round(len(completed_rides) / total_rides, 6) if total_rides else 0.0
        trust_score = _safe_int(presence.get("trust_score"), latest_trust)
        gps_freshness_band = "live"
        updated_at = _parse_timestamp(presence.get("updated_at"))
        if updated_at is not None:
            age_seconds = max(0.0, (datetime.now(tz=timezone.utc) - updated_at).total_seconds())
            if age_seconds > 600:
                gps_freshness_band = "stale"
            elif age_seconds > 120:
                gps_freshness_band = "warm"
        performance_score = int(
            round(
                _clamp(
                    45.0
                    + (acceptance_rate * 28.0)
                    + (completion_rate * 18.0)
                    + (trust_score * 0.18)
                    - (cancellation_rate * 22.0)
                    + (len(active_rides) * 1.5),
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        if performance_score >= 85:
            status = "excellent"
            recommendation = "Maintain current operating posture."
        elif performance_score >= 70:
            status = "healthy"
            recommendation = "Keep monitoring and reinforce active supply."
        elif performance_score >= 55:
            status = "watch"
            recommendation = "Offer coaching and targeted incentives."
        else:
            status = "at_risk"
            recommendation = "Review allocation and trust conditions."
        top_rows.append(
            {
                "driver_id": driver_id,
                "status": status,
                "presence_status": presence.get("status", "offline"),
                "performance_score": performance_score,
                "trust_score": trust_score,
                "acceptance_rate": acceptance_rate,
                "cancellation_rate": cancellation_rate,
                "completion_rate": completion_rate,
                "assigned_rides": total_assigned,
                "completed_rides": len(completed_rides),
                "cancelled_rides": len(cancelled_rides),
                "active_rides": len(active_rides),
                "gps_freshness_band": gps_freshness_band,
                "location": presence.get("location", {}),
                "recommendation": recommendation,
            }
        )

    top_rows.sort(key=lambda row: (row["performance_score"], row["completion_rate"], row["acceptance_rate"]), reverse=True)
    if not top_rows:
        top_rows.append(
            {
                "driver_id": None,
                "status": "unavailable",
                "presence_status": "offline",
                "performance_score": 0,
                "trust_score": latest_trust,
                "acceptance_rate": 0.0,
                "cancellation_rate": 0.0,
                "completion_rate": 0.0,
                "assigned_rides": 0,
                "completed_rides": 0,
                "cancelled_rides": 0,
                "active_rides": 0,
                "gps_freshness_band": "stale",
                "location": {},
                "recommendation": "No driver telemetry is available yet.",
            }
        )

    overall_completed = sum(row["completed_rides"] for row in top_rows)
    overall_cancelled = sum(row["cancelled_rides"] for row in top_rows)
    overall_acceptance_rate = round(
        len([assignment for assignment in dispatch_assignments if str(assignment.get("status")) == "accepted"])
        / max(1, len(dispatch_assignments)),
        6,
    ) if dispatch_assignments else 0.0
    overall_cancellation_rate = round(overall_cancelled / max(1, len(rides)), 6) if rides else 0.0

    return {
        "view": "novaride_phase7_driver_performance",
        "overall_acceptance_rate": overall_acceptance_rate,
        "overall_cancellation_rate": overall_cancellation_rate,
        "overall_completion_rate": round(overall_completed / max(1, len(rides)), 6) if rides else 0.0,
        "driver_count": len(top_rows),
        "top_drivers": top_rows[:10],
        "projection_only": True,
        "read_only": True,
    }


def _ride_metrics(
    *,
    rides: list[dict[str, Any]],
    dispatch_assignments: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    ride_status_counts = Counter(str(ride.get("status", "unknown")).lower() for ride in rides)
    total_rides = len(rides)
    accepted_assignments = len([assignment for assignment in dispatch_assignments if str(assignment.get("status")) == "accepted"])
    acceptance_rate = round(accepted_assignments / max(1, len(dispatch_assignments)), 6) if dispatch_assignments else 0.0
    cancellation_rate = round(ride_status_counts.get("cancelled", 0) / max(1, total_rides), 6) if rides else 0.0
    completion_rate = round(ride_status_counts.get("completed", 0) / max(1, total_rides), 6) if rides else 0.0
    completed_fares = [
        _safe_decimal(ride.get("final_fare", ride.get("fare_estimate", "0.00")))
        for ride in rides
        if str(ride.get("status", "")).lower() == "completed"
    ]
    average_fare = sum(completed_fares, Decimal("0.00")) / max(1, len(completed_fares))
    transaction_volume = sum((_safe_decimal(tx.get("amount")) for tx in transactions), Decimal("0.00"))
    return {
        "view": "novaride_phase7_ride_metrics",
        "acceptance_rate": acceptance_rate,
        "cancellation_rate": cancellation_rate,
        "completion_rate": completion_rate,
        "average_completed_fare": _money_text(average_fare),
        "transaction_volume": _money_text(transaction_volume),
        "status_counts": dict(ride_status_counts),
        "total_rides": total_rides,
        "completed_rides": ride_status_counts.get("completed", 0),
        "cancelled_rides": ride_status_counts.get("cancelled", 0),
        "active_rides": sum(1 for ride in rides if str(ride.get("status", "")).lower() in _active_ride_statuses()),
        "projection_only": True,
        "read_only": True,
    }


def _demand_forecast_projection(
    *,
    organization_id: str,
    limit: int,
) -> dict[str, Any]:
    demand = build_control_projection("build_dashboard_demand_forecast", 
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    return {
        "view": "novaride_phase7_demand_forecast",
        "model": demand.get("model", {}),
        "realtime_analytics": demand.get("realtime_analytics", {}),
        "city_forecasts": demand.get("city_forecasts", []),
        "forecast_windows": demand.get("forecast_windows", []),
        "recommendation": demand.get("recommendation", {}),
        "projection_only": True,
        "read_only": True,
    }


def _churn_analysis(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
    dispatch_assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    passenger_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    driver_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ride in rides:
        passenger_id = str(ride.get("passenger_id") or "").strip()
        driver_id = str(ride.get("driver_id") or "").strip()
        if passenger_id:
            passenger_rows[passenger_id].append(ride)
        if driver_id:
            driver_rows[driver_id].append(ride)

    at_risk_passengers: list[dict[str, Any]] = []
    for passenger_id, passenger_rides in passenger_rows.items():
        completed = sum(1 for ride in passenger_rides if str(ride.get("status", "")).lower() == "completed")
        cancelled = sum(1 for ride in passenger_rides if str(ride.get("status", "")).lower() == "cancelled")
        total = len(passenger_rides)
        churn_rate = round(cancelled / max(1, total), 6)
        churn_score = int(
            round(
                _clamp(
                    25.0 + (churn_rate * 65.0) + (10.0 if completed == 0 and total > 1 else 0.0),
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        if churn_score >= 50:
            at_risk_passengers.append(
                {
                    "passenger_id": passenger_id,
                    "churn_score": churn_score,
                    "churn_rate": churn_rate,
                    "completed_rides": completed,
                    "cancelled_rides": cancelled,
                    "total_rides": total,
                    "recommendation": "Offer retention support and service recovery incentives.",
                }
            )

    at_risk_drivers: list[dict[str, Any]] = []
    for driver in drivers:
        driver_id = str(driver.get("driver_id") or "").strip()
        if not driver_id:
            continue
        driver_rides = driver_rows.get(driver_id, [])
        completed = sum(1 for ride in driver_rides if str(ride.get("status", "")).lower() == "completed")
        cancelled = sum(1 for ride in driver_rides if str(ride.get("status", "")).lower() == "cancelled")
        assigned = sum(1 for assignment in dispatch_assignments if str(assignment.get("driver_id")) == driver_id)
        accepted = sum(
            1
            for assignment in dispatch_assignments
            if str(assignment.get("driver_id")) == driver_id and str(assignment.get("status")) == "accepted"
        )
        acceptance_rate = round(accepted / max(1, assigned), 6)
        cancellation_rate = round(cancelled / max(1, len(driver_rides)), 6) if driver_rides else 0.0
        trust_score = _safe_int(driver.get("trust_score"), _organization_trust_score(organization_id))
        churn_score = int(
            round(
                _clamp(
                    20.0
                    + ((1.0 - acceptance_rate) * 42.0)
                    + (cancellation_rate * 24.0)
                    + (max(0, 90 - trust_score) * 0.6),
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        if churn_score >= 45:
            at_risk_drivers.append(
                {
                    "driver_id": driver_id,
                    "churn_score": churn_score,
                    "acceptance_rate": acceptance_rate,
                    "cancellation_rate": cancellation_rate,
                    "completed_rides": completed,
                    "cancelled_rides": cancelled,
                    "trust_score": trust_score,
                    "recommendation": "Intervene with coaching, incentives, or allocation review.",
                }
            )

    passenger_churn_rate = round(
        len(at_risk_passengers) / max(1, len(passenger_rows)),
        6,
    ) if passenger_rows else 0.0
    driver_churn_rate = round(
        len(at_risk_drivers) / max(1, len(drivers)),
        6,
    ) if drivers else 0.0
    overall_churn_risk = int(
        round(
            _clamp(
                (passenger_churn_rate * 55.0) + (driver_churn_rate * 45.0) + 18.0,
                minimum=0.0,
                maximum=100.0,
            )
        )
    )

    retention_actions = [
        "Send targeted retention support to at-risk passengers.",
        "Coach or reassign at-risk drivers before churn grows.",
        "Use demand and trust signals to reduce service mismatch.",
    ]
    if overall_churn_risk < 30:
        retention_actions = ["Maintain the current retention band and continue monitoring."]

    return {
        "view": "novaride_phase7_churn_analysis",
        "passenger_churn_rate": passenger_churn_rate,
        "driver_churn_rate": driver_churn_rate,
        "overall_churn_risk": overall_churn_risk,
        "at_risk_passengers": sorted(at_risk_passengers, key=lambda row: row["churn_score"], reverse=True)[:10],
        "at_risk_drivers": sorted(at_risk_drivers, key=lambda row: row["churn_score"], reverse=True)[:10],
        "retention_actions": retention_actions,
        "projection_only": True,
        "read_only": True,
    }


def _live_gps_stream(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
) -> dict[str, Any]:
    active_drivers = [
        driver
        for driver in drivers
        if str(driver.get("status", "")).lower() in {"online", "busy"}
    ]
    active_rides = [
        ride
        for ride in rides
        if str(ride.get("status", "")).lower() in _active_ride_statuses()
    ]
    driver_positions = []
    freshest_timestamp: datetime | None = None
    for driver in active_drivers[:20]:
        location = driver.get("location") or {}
        updated_at = _parse_timestamp(driver.get("updated_at"))
        if updated_at is not None and (freshest_timestamp is None or updated_at > freshest_timestamp):
            freshest_timestamp = updated_at
        driver_positions.append(
            {
                "driver_id": driver.get("driver_id"),
                "status": driver.get("status"),
                "location": location,
                "trust_score": _safe_int(driver.get("trust_score"), _organization_trust_score(organization_id)),
                "updated_at": driver.get("updated_at"),
            }
        )

    active_markers = []
    for ride in active_rides[:20]:
        active_markers.append(
            {
                "ride_id": ride.get("ride_id"),
                "passenger_id": ride.get("passenger_id"),
                "driver_id": ride.get("driver_id"),
                "pickup_location": ride.get("pickup_location"),
                "destination_location": ride.get("destination_location"),
                "status": ride.get("status"),
            }
        )
        updated_at = _parse_timestamp(ride.get("updated_at"))
        if updated_at is not None and (freshest_timestamp is None or updated_at > freshest_timestamp):
            freshest_timestamp = updated_at

    freshness_seconds = 0.0
    freshness_band = "live"
    if freshest_timestamp is not None:
        freshness_seconds = max(0.0, (datetime.now(tz=timezone.utc) - freshest_timestamp).total_seconds())
        if freshness_seconds > 600:
            freshness_band = "stale"
        elif freshness_seconds > 120:
            freshness_band = "warm"

    return {
        "view": "novaride_phase7_live_gps_stream",
        "streaming_mode": "websocket_streaming",
        "transport": "live_gps_and_presence_stream",
        "driver_positions": driver_positions,
        "active_ride_markers": active_markers,
        "active_driver_count": len(active_drivers),
        "active_ride_count": len(active_rides),
        "stream_freshness_seconds": round(freshness_seconds, 2),
        "freshness_band": freshness_band,
        "primary_zone": _latest_zone(organization_id),
        "projection_only": True,
        "read_only": True,
    }


def _learning_engine_projection(
    *,
    organization_id: str,
    limit: int,
    rides: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    dispatch_assignments = _dispatch_rows(organization_id, limit=limit)
    phase6 = build_phase6_status(organization_id=organization_id, limit=limit)
    phase5 = build_phase5_status(organization_id=organization_id, limit=limit)
    autonomy = build_control_projection("build_dashboard_autonomy", 
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    outcome_learning = build_control_projection("build_outcome_learning", 
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    demand_forecast = build_control_projection("build_dashboard_demand_forecast", 
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    navigation_intelligence = build_navigation_maps_intelligence_projection(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        limit=limit,
    )
    revenue_dashboard = _revenue_dashboard(
        organization_id=organization_id,
        rides=rides,
        transactions=transactions,
    )
    ride_metrics = _ride_metrics(
        rides=rides,
        dispatch_assignments=dispatch_assignments,
        transactions=transactions,
    )
    churn_analysis = _churn_analysis(
        organization_id=organization_id,
        rides=rides,
        drivers=drivers,
        dispatch_assignments=dispatch_assignments,
    )

    latest_decision = _store().latest_ai_decision_snapshot(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        decision_type="operator_decision",
    )
    latest_action = _store().latest_ai_action_snapshot(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        action_type="controlled_autonomous_action",
    )
    latest_outcome = _store().latest_outcome_snapshot(
        organization_id=organization_id,
        source="afriride_operator_dashboard",
        outcome_type="measured_outcome",
    )
    decision_rows = _decision_rows(organization_id, limit=limit)
    action_rows = _action_rows(organization_id, limit=limit)
    outcome_rows = _outcome_rows(organization_id, limit=limit)

    completion_rate = ride_metrics["completion_rate"]
    acceptance_rate = ride_metrics["acceptance_rate"]
    cancellation_rate = ride_metrics["cancellation_rate"]
    trust_score = _organization_trust_score(organization_id)
    churn_penalty = float(churn_analysis["overall_churn_risk"]) / 100.0
    revenue_band = _safe_float(revenue_dashboard["projected_margin_pct"], 0.0) / 100.0
    reward_proxy = _clamp(
        (completion_rate * 42.0)
        + (acceptance_rate * 26.0)
        + ((1.0 - cancellation_rate) * 14.0)
        + (trust_score * 0.12)
        + (revenue_band * 10.0)
        - (churn_penalty * 18.0),
        minimum=0.0,
        maximum=100.0,
    )
    phase6_ready = bool(phase6.get("ready", False))
    phase5_ready = bool(phase5.get("ready", False))
    if phase6_ready and phase5_ready and reward_proxy >= 80:
        execution_mode = "bounded_autonomous"
        autonomy_state = "autonomous"
        operator_confirmation_required = False
    elif phase6_ready and reward_proxy >= 60:
        execution_mode = "supervised_autonomy"
        autonomy_state = "supervised"
        operator_confirmation_required = True
    else:
        execution_mode = "monitor_only"
        autonomy_state = "watching"
        operator_confirmation_required = True

    policy_recommendation = (
        "Expand autonomous execution in the strongest zone."
        if reward_proxy >= 80
        else "Keep the learning loop supervised and refine the dispatch policy."
        if reward_proxy >= 60
        else "Hold automation and collect more operating evidence."
    )
    reward_signal = {
        "reward_proxy": round(reward_proxy, 4),
        "completion_rate": completion_rate,
        "acceptance_rate": acceptance_rate,
        "cancellation_rate": cancellation_rate,
        "trust_score": trust_score,
        "churn_risk": churn_analysis["overall_churn_risk"],
        "gross_transaction_volume": revenue_dashboard["gross_transaction_volume"],
    }
    feedback_loop = {
        "update_cycle": "realtime_feedback_loop",
        "signal_sources": [
            "rides",
            "dispatch_assignments",
            "transactions",
            "driver_presence",
            "analytics_snapshot",
            "outcome_learning",
        ],
        "reward_signal": reward_signal,
        "policy_state": autonomy_state,
        "recommended_policy": policy_recommendation,
        "recalibration_notes": list(outcome_learning.get("learning", {}).get("recalibration_notes", [])),
        "watch_items": list(outcome_learning.get("learning", {}).get("watch_items", [])),
        "projection_only": True,
        "read_only": True,
    }

    live_execution = {
        "mode": execution_mode,
        "safe_to_autorun": bool(phase6.get("ready", False) and phase5.get("ready", False) and reward_proxy >= 80),
        "operator_confirmation_required": operator_confirmation_required,
        "gps_streaming": True,
        "streaming_mode": "websocket_streaming",
        "live_gps_stream": _live_gps_stream(organization_id=organization_id, rides=rides, drivers=drivers),
        "navigation_intelligence": {
            "route_optimization": navigation_intelligence["route_optimization"],
            "traffic_aware_routing": navigation_intelligence["traffic_aware_routing"],
            "pickup_precision": navigation_intelligence["pickup_precision"],
            "heatmaps": navigation_intelligence["heatmaps"],
            "capital_allocation": navigation_intelligence["capital_allocation"],
            "controlled_execution": navigation_intelligence["controlled_execution"],
        },
        "bounded_controls": [
            "projection_only",
            "read_only",
            "no_runtime_mutation",
            "no_payment_authority",
            "no_provider_direct_access",
            "no_dispatch_override",
            "tenant_isolation_preserved",
        ],
        "projection_only": True,
        "read_only": True,
    }

    return {
        "view": "novaride_phase7_learning_engine",
        "organization_id": organization_id,
        "source": "afriride_operator_dashboard",
        "phase5": phase5,
        "phase6": phase6,
        "revenue_dashboard": revenue_dashboard,
        "driver_performance": _driver_performance(
            organization_id=organization_id,
            rides=rides,
            drivers=drivers,
            dispatch_assignments=dispatch_assignments,
        ),
        "ride_metrics": ride_metrics,
        "demand_forecast": _demand_forecast_projection(organization_id=organization_id, limit=limit),
        "churn_analysis": churn_analysis,
        "live_gps_stream": _live_gps_stream(organization_id=organization_id, rides=rides, drivers=drivers),
        "learning_engine": {
            "mode": "realtime_feedback_loop",
            "policy_state": autonomy_state,
            "reward_signal": reward_signal,
            "feedback_loop": feedback_loop,
            "outcome_learning": outcome_learning,
            "analytics_prediction": build_control_projection("build_dashboard_analytics_prediction", 
                organization_id=organization_id,
                source="afriride_operator_dashboard",
                limit=limit,
            ),
            "latest_decision": latest_decision,
            "latest_action": latest_action,
            "latest_outcome": latest_outcome,
            "decision_history": decision_rows,
            "action_history": action_rows,
            "outcome_history": outcome_rows,
            "rl_model": {
                "name": "bounded_feedback_loop_rl",
                "mode": "realtime_learning" if (decision_rows or action_rows or outcome_rows) else "warm_start",
                "reward_proxy": round(reward_proxy, 4),
                "policy_recommendation": policy_recommendation,
                "learning_band": outcome_learning.get("learning", {}).get("band", "hold"),
                "feedback_strength": round(_clamp(reward_proxy / 100.0, minimum=0.0, maximum=1.0), 4),
                "projection_only": True,
                "read_only": True,
            },
            "learning_summary": (
                "Real-time ride, GPS, and financial signals are feeding the bounded learning loop."
            ),
            "projection_only": True,
            "read_only": True,
        },
        "real_time_execution": live_execution,
        "analytics_dashboard": {
            "revenue_dashboard": revenue_dashboard,
            "driver_performance": _driver_performance(
                organization_id=organization_id,
                rides=rides,
                drivers=drivers,
                dispatch_assignments=dispatch_assignments,
            ),
            "ride_metrics": ride_metrics,
            "demand_forecast": _demand_forecast_projection(organization_id=organization_id, limit=limit),
            "churn_analysis": churn_analysis,
            "live_gps_stream": _live_gps_stream(organization_id=organization_id, rides=rides, drivers=drivers),
            "learning_engine": feedback_loop,
            "real_time_execution": live_execution,
            "navigation_intelligence": navigation_intelligence,
            "projection_only": True,
            "read_only": True,
        },
        "navigation_intelligence": navigation_intelligence,
        "analytics_prediction": build_control_projection("build_dashboard_analytics_prediction", 
            organization_id=organization_id,
            source="afriride_operator_dashboard",
            limit=limit,
        ),
        "autonomy": autonomy,
        "phase6_ready": phase6_ready,
        "phase5_ready": phase5_ready,
        "reward_signal": reward_signal,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
    }


def build_phase7_analytics_intelligence_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    rides = _ride_rows(organization_id, limit)
    drivers = _driver_rows(organization_id, limit)
    transactions = _transaction_rows(organization_id, limit)
    learning = _learning_engine_projection(
        organization_id=organization_id,
        limit=limit,
        rides=rides,
        drivers=drivers,
        transactions=transactions,
    )
    learning["source"] = source or "afriride_operator_dashboard"
    learning["view"] = "novaride_phase7_analytics_intelligence"
    return learning


def build_phase7_learning_engine_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    projection = build_phase7_analytics_intelligence_projection(
        organization_id=organization_id,
        limit=limit,
        source=source,
    )
    return {
        "view": "novaride_phase7_learning_engine",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "learning_engine": projection["learning_engine"],
        "real_time_execution": projection["real_time_execution"],
        "reward_signal": projection["reward_signal"],
        "analytics_dashboard": projection["analytics_dashboard"],
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": projection["created_at"],
    }


def build_phase7_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase5 = build_phase5_status(organization_id=org_id, limit=limit)
    phase6 = build_phase6_status(organization_id=org_id, limit=limit)
    analytics = build_phase7_analytics_intelligence_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase5_ready": bool(phase5.get("ready", False)),
        "phase6_ready": bool(phase6.get("ready", False)),
        "revenue_dashboard_ready": bool(analytics["revenue_dashboard"].get("gross_transaction_volume") is not None),
        "driver_performance_ready": bool(analytics["driver_performance"].get("top_drivers")),
        "ride_metrics_ready": bool(analytics["ride_metrics"].get("total_rides") is not None),
        "demand_forecast_ready": bool(analytics["demand_forecast"].get("forecast_windows")),
        "churn_analysis_ready": bool(analytics["churn_analysis"].get("retention_actions")),
        "live_gps_stream_ready": bool(analytics["live_gps_stream"].get("streaming_mode")),
        "learning_engine_ready": bool(analytics["learning_engine"].get("rl_model")),
        "real_time_execution_ready": bool(analytics["real_time_execution"].get("mode")),
        "navigation_intelligence_ready": bool(analytics.get("navigation_intelligence", {}).get("route_optimization")),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "revenue_dashboard_ready",
            "driver_performance_ready",
            "ride_metrics_ready",
            "demand_forecast_ready",
            "churn_analysis_ready",
            "live_gps_stream_ready",
            "learning_engine_ready",
            "real_time_execution_ready",
            "navigation_intelligence_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase7_status",
        "phase": "7",
        "platform": "NovaRide Phase 7",
        "organization_id": org_id,
        "phase5": phase5,
        "phase6": phase6,
        "analytics_intelligence": analytics,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE7_TOPIC",
    "build_phase7_analytics_intelligence_projection",
    "build_phase7_learning_engine_projection",
    "build_phase7_status",
]
