"""NovaRide Phase 6 navigation and maps intelligence.

This layer is projection-only. It synthesizes route optimization, traffic-aware
routing, pickup precision, demand heatmaps, and capital allocation / ROI
recommendations without mutating runtime dispatch authority.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase4 import (
    build_business_budget_allocation_projection,
    build_business_profit_optimization_projection,
    build_phase4_status,
)
from afritech.afriprogramming.phase5 import build_phase5_status


PHASE6_TOPIC = "novaride.phase6.navigation_maps_intelligence"


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


def _latest_zone(organization_id: str) -> str:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)
    return "CBD"


def _location_zone(location: dict[str, Any] | None, fallback_zone: str) -> str:
    if not isinstance(location, dict):
        return fallback_zone
    for key in ("label", "name", "zone", "city", "suburb", "area"):
        value = location.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback_zone


def _heatmap_weight(status: str | None) -> float:
    normalized = str(status or "").lower()
    if normalized in {"requested", "matched", "arriving", "in_progress"}:
        return 1.0
    if normalized == "completed":
        return 0.45
    if normalized == "cancelled":
        return 0.2
    return 0.6


def _zone_rows(
    *,
    organization_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rides = _store().list_rides(organization_id=organization_id, limit=limit)
    drivers = _store().list_driver_presence(organization_id=organization_id, limit=limit)
    fallback_zone = _latest_zone(organization_id)

    ride_buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"demand_weight": 0.0, "rides": 0, "active_rides": 0, "pickup_hits": 0})
    driver_buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"drivers": 0, "online_drivers": 0, "trust_total": 0.0})

    for ride in rides:
        pickup_zone = _location_zone(ride.get("pickup_location"), fallback_zone)
        dropoff_zone = _location_zone(ride.get("destination_location"), fallback_zone)
        weight = _heatmap_weight(ride.get("status"))
        ride_buckets[pickup_zone]["demand_weight"] += weight
        ride_buckets[pickup_zone]["rides"] += 1
        ride_buckets[pickup_zone]["pickup_hits"] += 1
        if ride.get("status") != "completed":
            ride_buckets[pickup_zone]["active_rides"] += 1
        if dropoff_zone != pickup_zone:
            ride_buckets[dropoff_zone]["demand_weight"] += max(0.25, weight * 0.35)

    for driver in drivers:
        zone = _location_zone(driver.get("location"), fallback_zone)
        driver_buckets[zone]["drivers"] += 1
        if str(driver.get("status")) == "online":
            driver_buckets[zone]["online_drivers"] += 1
        driver_buckets[zone]["trust_total"] += float(driver.get("trust_score") or 0.0)

    zones = sorted(set(ride_buckets) | set(driver_buckets)) or [fallback_zone]
    latest_trust = _store().latest_trust_score(organization_id=organization_id)
    org_trust = int(latest_trust.get("trust_score") if latest_trust else 92)

    rows: list[dict[str, Any]] = []
    for zone in zones:
        ride_row = ride_buckets.get(zone, {})
        driver_row = driver_buckets.get(zone, {})
        demand_rides = int(ride_row.get("rides", 0))
        active_rides = int(ride_row.get("active_rides", 0))
        active_drivers = int(driver_row.get("online_drivers", 0))
        total_drivers = int(driver_row.get("drivers", 0))
        demand_weight = float(ride_row.get("demand_weight", 0.0))
        supply_weight = max(1.0, float(active_drivers) + (float(total_drivers) * 0.35))
        pressure_index = round(demand_weight / supply_weight, 4)
        traffic_index = round((demand_weight * 1.2) + (active_rides * 0.6) - (active_drivers * 0.4), 4)
        pickup_precision_score = int(
            round(
                _clamp(
                    60.0 + (demand_rides * 6.0) + (active_drivers * 4.0) + (org_trust * 0.2),
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        route_efficiency_score = int(
            round(
                _clamp(
                    55.0 + (demand_weight * 8.0) + (active_drivers * 5.0) - (active_rides * 2.0),
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        eta_bias = round(max(0.0, traffic_index * 2.5), 2)
        if pressure_index >= 1.8:
            route_lane = "optimize_supply"
            recommendation = f"Reposition drivers toward {zone}"
            reason = "Demand pressure exceeds current supply."
        elif traffic_index >= 5.0:
            route_lane = "optimize_traffic"
            recommendation = f"Use traffic-aware routing around {zone}"
            reason = "Traffic pressure is likely to raise ETAs."
        elif pickup_precision_score < 75:
            route_lane = "improve_pickup_precision"
            recommendation = f"Request pin confirmation for pickups near {zone}"
            reason = "Pickup accuracy can improve matching quality."
        else:
            route_lane = "monitor"
            recommendation = f"Maintain current coverage around {zone}"
            reason = "The zone is within controlled operating limits."

        roi_base = (demand_weight * 2.2) + (pickup_precision_score * 0.45) + (route_efficiency_score * 0.35)
        allocation_factor = max(1.0, (pressure_index * 0.65) + (traffic_index * 0.08))
        recommended_capital_allocation = _money_text(Decimal(str(roi_base * allocation_factor * 12.0)))
        projected_roi = round(_clamp((roi_base / 10.0) - (traffic_index * 0.08), minimum=0.0, maximum=5.0), 4)

        rows.append(
            {
                "zone": zone,
                "rides": demand_rides,
                "active_rides": active_rides,
                "active_drivers": active_drivers,
                "total_drivers": total_drivers,
                "demand_weight": round(demand_weight, 4),
                "pressure_index": pressure_index,
                "traffic_index": traffic_index,
                "pickup_precision_score": pickup_precision_score,
                "route_efficiency_score": route_efficiency_score,
                "route_lane": route_lane,
                "recommendation": recommendation,
                "reason": reason,
                "eta_bias_minutes": eta_bias,
                "recommended_capital_allocation": recommended_capital_allocation,
                "projected_roi": projected_roi,
                "roi_band": "strong" if projected_roi >= 2.5 else "moderate" if projected_roi >= 1.5 else "guarded",
            }
        )

    rows.sort(key=lambda row: (row["pressure_index"], row["traffic_index"], row["pickup_precision_score"]), reverse=True)
    return rows


def _traffic_profile(zone_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not zone_rows:
        return {
            "mode": "light",
            "traffic_level": "low",
            "traffic_index": 0.0,
            "eta_reduction_target_minutes": 0.0,
        }
    peak = zone_rows[0]
    traffic_index = float(peak["traffic_index"])
    if traffic_index >= 10:
        level = "heavy"
    elif traffic_index >= 5:
        level = "moderate"
    else:
        level = "low"
    eta_reduction_target = round(min(12.0, max(0.0, 2.0 + (peak["pickup_precision_score"] / 20.0))), 2)
    return {
        "mode": "traffic_aware",
        "traffic_level": level,
        "traffic_index": round(traffic_index, 4),
        "peak_zone": peak["zone"],
        "eta_reduction_target_minutes": eta_reduction_target,
        "recommended_route_lane": peak["route_lane"],
        "recommended_action": peak["recommendation"],
    }


def _pickup_precision_profile(zone_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not zone_rows:
        return {
            "mode": "baseline",
            "precision_score": 0,
            "pin_adjustment_required": False,
            "recommendation": "No pickup signals available yet.",
        }
    average_precision = round(sum(row["pickup_precision_score"] for row in zone_rows) / len(zone_rows), 2)
    pin_adjustment_required = average_precision < 80
    return {
        "mode": "pin_adjusted" if pin_adjustment_required else "exact",
        "precision_score": average_precision,
        "pin_adjustment_required": pin_adjustment_required,
        "recommendation": (
            "Confirm pickup pins before dispatching drivers."
            if pin_adjustment_required
            else "Pickup precision is within the target band."
        ),
        "best_precision_zone": zone_rows[0]["zone"],
    }


def _heatmap_profile(zone_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not zone_rows:
        return {
            "mode": "empty",
            "zones": [],
            "hotspots": [],
        }
    hotspots = [row for row in zone_rows if row["pressure_index"] >= 1.4 or row["traffic_index"] >= 5]
    return {
        "mode": "demand_heatmap",
        "zones": zone_rows,
        "hotspots": hotspots,
        "primary_zone": zone_rows[0]["zone"],
        "zone_count": len(zone_rows),
    }


def _capital_allocation_profile(
    *,
    organization_id: str,
    zone_rows: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    budget = build_business_budget_allocation_projection(organization_id=organization_id, limit=limit)
    profit = build_business_profit_optimization_projection(organization_id=organization_id, limit=limit)
    demand = build_control_projection("build_dashboard_demand_forecast", organization_id=organization_id, limit=limit)
    city_allocations = budget.get("budget_allocation", {}).get("city_allocations", [])
    pressure_by_city = {str(row["zone"]): row for row in zone_rows}
    allocation_rows: list[dict[str, Any]] = []
    for city_allocation in city_allocations:
        city = str(city_allocation.get("city"))
        zone_row = pressure_by_city.get(city, {})
        pressure_index = float(zone_row.get("pressure_index", 0.0))
        roi_score = float(zone_row.get("projected_roi", 0.0))
        recommended_capital = zone_row.get("recommended_capital_allocation") or city_allocation.get("recommended_budget") or "0.00"
        allocation_rows.append(
            {
                "city": city,
                "zone": city,
                "recommended_capital_allocation": recommended_capital,
                "projected_roi": roi_score,
                "pressure_index": round(pressure_index, 4),
                "profit_projection": city_allocation.get("projected_profit", profit.get("profit_optimization", {}).get("projected_profit")),
                "budget_signal": city_allocation.get("budget_status", budget.get("budget_allocation", {}).get("mode")),
                "recommendation": (
                    f"Allocate more capital to {city}"
                    if pressure_index >= 1.4
                    else f"Hold capital allocation around {city}"
                ),
            }
        )
    allocation_rows.sort(key=lambda row: (row["projected_roi"], row["pressure_index"]), reverse=True)
    total_roi = round(sum(row["projected_roi"] for row in allocation_rows), 4)
    recommended_allocation = sum(
        float(str(row["recommended_capital_allocation"]).replace(",", "")) if row["recommended_capital_allocation"] else 0.0
        for row in allocation_rows
    )
    return {
        "mode": budget.get("budget_allocation", {}).get("mode", "supervised"),
        "capital_allocation": allocation_rows,
        "budget_projection": budget.get("budget_allocation", {}),
        "profit_projection": profit.get("profit_optimization", {}),
        "demand_forecast": demand,
        "recommended_capital_total": _money_text(recommended_allocation),
        "roi_score": round(total_roi, 4),
        "roi_band": "strong" if total_roi >= 8.0 else "moderate" if total_roi >= 4.0 else "guarded",
        "projection_only": True,
        "read_only": True,
    }


def build_navigation_maps_intelligence_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    phase5 = build_phase5_status(organization_id=organization_id, limit=limit)
    phase4 = build_phase4_status(organization_id=organization_id, limit=limit)
    zone_rows = _zone_rows(organization_id=organization_id, limit=limit)
    traffic_profile = _traffic_profile(zone_rows)
    pickup_precision = _pickup_precision_profile(zone_rows)
    heatmaps = _heatmap_profile(zone_rows)
    capital_allocation = _capital_allocation_profile(organization_id=organization_id, zone_rows=zone_rows, limit=limit)
    autonomy = build_control_projection("build_dashboard_autonomy", organization_id=organization_id, limit=limit)
    demand_forecast = build_control_projection("build_dashboard_demand_forecast", organization_id=organization_id, limit=limit)

    route_optimization = {
        "mode": "traffic_aware" if traffic_profile["traffic_level"] != "low" else "balanced",
        "primary_zone": heatmaps.get("primary_zone", _latest_zone(organization_id)),
        "best_route_zone": traffic_profile.get("peak_zone", _latest_zone(organization_id)),
        "route_lane": traffic_profile["recommended_route_lane"],
        "eta_reduction_target_minutes": traffic_profile["eta_reduction_target_minutes"],
        "pickup_precision_score": pickup_precision["precision_score"],
        "recommendation": traffic_profile["recommended_action"],
        "reason": (
            "Traffic pressure suggests a route optimization opportunity."
            if traffic_profile["traffic_level"] != "low"
            else "Routing remains within controlled bounds."
        ),
        "route_rows": zone_rows,
        "projection_only": True,
        "read_only": True,
    }

    controlled_execution = {
        "mode": "controlled",
        "safe_to_autorun": bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False) and phase5.get("ready", False)),
        "operator_confirmation_required": not bool(autonomy.get("autonomy", {}).get("safe_to_autorun", False)),
        "safe_limit_rules": {
            "projection_only": True,
            "read_only": True,
            "no_runtime_mutation": True,
            "no_payment_authority": True,
            "no_provider_direct_access": True,
            "no_dispatch_override": True,
            "tenant_isolation_preserved": True,
            "max_route_lane": "traffic_aware",
            "max_capital_reallocation": "bounded",
        },
        "recommendation": "Use bounded execution only after operator confirmation and phase 5 safety clearance.",
        "projection_only": True,
        "read_only": True,
    }

    maps_intelligence = {
        "route_optimization": route_optimization,
        "traffic_aware_routing": traffic_profile,
        "pickup_precision": pickup_precision,
        "heatmaps": heatmaps,
        "capital_allocation": capital_allocation,
        "controlled_execution": controlled_execution,
        "autonomy": autonomy,
        "demand_forecast": demand_forecast,
        "phase4": phase4,
        "phase5": phase5,
    }

    readiness = {
        "phase5_ready": bool(phase5.get("ready", False)),
        "phase4_ready": bool(phase4.get("ready", False)),
        "route_optimization_ready": bool(zone_rows),
        "traffic_aware_routing_ready": bool(traffic_profile.get("mode")),
        "pickup_precision_ready": bool(pickup_precision.get("mode")),
        "heatmaps_ready": bool(heatmaps.get("zones")),
        "capital_allocation_ready": bool(capital_allocation.get("capital_allocation")),
        "controlled_execution_ready": bool(controlled_execution.get("mode")),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "route_optimization_ready",
            "traffic_aware_routing_ready",
            "pickup_precision_ready",
            "heatmaps_ready",
            "capital_allocation_ready",
            "controlled_execution_ready",
            "tenant_isolation_preserved",
        )
    )

    return {
        "view": "novaride_phase6_navigation_maps_intelligence",
        "phase": "6",
        "platform": "NovaRide Phase 6",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "maps_intelligence": maps_intelligence,
        "route_optimization": route_optimization,
        "traffic_aware_routing": traffic_profile,
        "pickup_precision": pickup_precision,
        "heatmaps": heatmaps,
        "capital_allocation": capital_allocation,
        "controlled_execution": controlled_execution,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
    }


def build_phase6_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase4 = build_phase4_status(organization_id=org_id, limit=limit)
    phase5 = build_phase5_status(organization_id=org_id, limit=limit)
    navigation = build_navigation_maps_intelligence_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase5_ready": bool(phase5.get("ready", False)),
        "phase4_ready": bool(phase4.get("ready", False)),
        "route_optimization_ready": bool(navigation["route_optimization"].get("route_rows")),
        "traffic_aware_routing_ready": bool(navigation["traffic_aware_routing"].get("mode")),
        "pickup_precision_ready": bool(navigation["pickup_precision"].get("mode")),
        "heatmaps_ready": bool(navigation["heatmaps"].get("zones")),
        "capital_allocation_ready": bool(navigation["capital_allocation"].get("capital_allocation")),
        "controlled_execution_ready": bool(navigation["controlled_execution"].get("mode")),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "route_optimization_ready",
            "traffic_aware_routing_ready",
            "pickup_precision_ready",
            "heatmaps_ready",
            "capital_allocation_ready",
            "controlled_execution_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase6_status",
        "phase": "6",
        "platform": "NovaRide Phase 6",
        "organization_id": org_id,
        "phase4": phase4,
        "phase5": phase5,
        "navigation": navigation,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE6_TOPIC",
    "build_navigation_maps_intelligence_projection",
    "build_phase6_status",
]
