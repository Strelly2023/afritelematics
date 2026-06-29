"""Projection-only intelligence feeds for driver and passenger mobile apps."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase6 import build_navigation_maps_intelligence_projection
from afritech.afriprogramming.phase7 import build_phase7_analytics_intelligence_projection
from afritech.afriprogramming.phase3 import build_business_pricing_projection
from afritech.afriprogramming.phase4 import build_business_budget_allocation_projection


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _store():
    return phase0_control_plane._STORE


def _safe_latest(sequence: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    for item in sequence:
        return item
    return None


def _demand_level(active_rides: int, active_drivers: int) -> str:
    if active_rides >= 5 and active_drivers <= 2:
        return "high"
    if active_rides >= 2:
        return "moderate"
    return "low"


def _surge_multiplier(demand_level: str) -> float:
    if demand_level == "high":
        return 1.8
    if demand_level == "moderate":
        return 1.3
    return 1.0


def _predictive_positioning(
    *,
    organization_id: str,
    zone: str,
    demand_level: str,
    trust_score: int,
    active_drivers: int,
) -> dict[str, Any]:
    if demand_level == "high" and active_drivers > 0 and trust_score >= 90:
        return {
            "mode": "fully_autonomous",
            "target_zone": zone,
            "confidence": 0.93,
            "instruction": f"Move toward {zone} now",
            "reason": "High demand and trusted supply support autonomous positioning",
            "projection_only": True,
            "read_only": True,
        }
    if demand_level == "moderate" and active_drivers > 0:
        return {
            "mode": "guided",
            "target_zone": zone,
            "confidence": 0.78,
            "instruction": f"Stay near {zone} for steady coverage",
            "reason": "Demand is stable enough for guided positioning",
            "projection_only": True,
            "read_only": True,
        }
    return {
        "mode": "held",
        "target_zone": zone,
        "confidence": 0.55,
        "instruction": "Maintain current position until the system detects stronger demand",
        "reason": "Autonomous positioning is not yet justified",
        "projection_only": True,
        "read_only": True,
    }


def _city_automation_projection(
    *,
    organization_id: str,
    zone: str,
    demand_level: str,
    trust_score: int,
    active_drivers: int,
    active_rides: int,
) -> dict[str, Any]:
    coverage_score = min(
        100,
        (active_drivers * 20)
        + (active_rides * 5)
        + (trust_score // 2)
        + (10 if demand_level == "high" else 5 if demand_level == "moderate" else 0),
    )
    zero_operator_mode = bool(active_drivers >= 3 and trust_score >= 90 and coverage_score >= 70)
    if zero_operator_mode:
        mode = "zero_operator"
        instruction = f"Keep city-wide automation active around {zone}"
        reason = "City coverage, trust, and supply support zero-operator mode"
    elif active_drivers >= 2 and trust_score >= 85:
        mode = "city_autonomous"
        instruction = f"Rebalance city supply toward {zone}"
        reason = "Supply is healthy enough for autonomous city balancing"
    elif active_drivers > 0:
        mode = "city_supervised"
        instruction = f"Hold supervised automation around {zone}"
        reason = "City automation remains projection-only"
    else:
        mode = "city_held"
        instruction = "Hold city automation until more drivers come online"
        reason = "No active city supply is available"
    return {
        "mode": mode,
        "zero_operator_mode": zero_operator_mode,
        "coverage_score": coverage_score,
        "active_drivers": active_drivers,
        "active_rides": active_rides,
        "city_zones": [zone],
        "recommended_zone": zone,
        "instruction": instruction,
        "reason": reason,
        "prediction": {
            "city_zone_count": 1,
            "city_trust_score": trust_score,
            "coverage_score": coverage_score,
            "demand_level": demand_level,
        },
        "projection_only": True,
        "read_only": True,
    }


def _multi_city_orchestration_projection(
    *,
    organization_id: str,
    zone: str,
    demand_level: str,
    trust_score: int,
    active_drivers: int,
    active_rides: int,
) -> dict[str, Any]:
    city_count = 2 if active_drivers >= 3 else 1
    global_coverage = min(100, 55 + (active_drivers * 8) + (active_rides * 3) + (trust_score // 3))
    mode = (
        "global_zero_operator"
        if active_drivers >= 3 and global_coverage >= 75
        else "global_autonomous"
        if active_drivers >= 2 and global_coverage >= 60
        else "global_supervised"
        if active_drivers > 0
        else "global_held"
    )
    if mode == "global_zero_operator":
        instruction = f"Keep multi-city orchestration active and optimize supply across {zone} and adjacent cities"
        reason = "Global coverage and supply are sufficient for zero-operator orchestration"
    elif mode == "global_autonomous":
        instruction = f"Autonomously balance active cities around {zone}"
        reason = "Multi-city supply is healthy enough for autonomous orchestration"
    elif mode == "global_supervised":
        instruction = f"Monitor city balance around {zone} under supervision"
        reason = "Orchestration remains projection-only"
    else:
        instruction = "Hold global orchestration until more cities come online"
        reason = "No active multi-city supply is available"
    return {
        "mode": mode,
        "city_count": city_count,
        "active_city_count": city_count if active_drivers > 0 else 0,
        "global_coverage_score": global_coverage,
        "global_trust_score": trust_score,
        "instruction": instruction,
        "reason": reason,
        "prediction": {
            "city_count": city_count,
            "active_city_count": city_count if active_drivers > 0 else 0,
            "coverage_score": global_coverage,
            "trust_score": trust_score,
            "demand_level": demand_level,
        },
        "projection_only": True,
        "read_only": True,
    }


def _latest_alerts(*, organization_id: str, limit: int = 3) -> list[str]:
    alerts = _store().list_assurance_alerts(organization_id=organization_id, limit=limit)
    if alerts:
        return [
            str(item.get("message") or item.get("alert_level") or "Operational alert")
            for item in alerts[:limit]
        ]
    return []


def _latest_zone(*, organization_id: str) -> str:
    drivers = _store().list_driver_presence(organization_id=organization_id, limit=1)
    latest_driver = _safe_latest(drivers)
    if latest_driver:
        location = latest_driver.get("location") or {}
        label = str(location.get("label") or location.get("name") or "").strip()
        if label:
            return label
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    payload = snapshot.get("payload", {}) if snapshot else {}
    if isinstance(payload, dict):
        zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
        if zone:
            return str(zone)
    return "CBD"


def _latest_trust_score(*, organization_id: str) -> int:
    trust = _store().latest_trust_score(organization_id=organization_id)
    if trust is not None:
        try:
            return int(trust.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        return int(snapshot.get("trust_score") or 92)
    return 92


def _compliance_summary(*, organization_id: str) -> dict[str, str]:
    trust_score = _latest_trust_score(organization_id=organization_id)
    alert_count = len(_latest_alerts(organization_id=organization_id, limit=5))
    if trust_score >= 90 and alert_count == 0:
        return {
            "vehicle": "verified",
            "documents": "valid",
            "inspection": "passed",
        }
    if trust_score >= 85:
        return {
            "vehicle": "verified",
            "documents": "review",
            "inspection": "passed",
        }
    return {
        "vehicle": "review",
        "documents": "review",
        "inspection": "review",
    }


def _active_counts(*, organization_id: str) -> tuple[int, int]:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        try:
            total_rides = int(snapshot.get("total_rides") or 0)
            completed_rides = int(snapshot.get("completed_rides") or 0)
            active_drivers = int(snapshot.get("active_drivers") or 0)
            return max(0, total_rides - completed_rides), active_drivers
        except (TypeError, ValueError):
            pass
    active_drivers = len(
        [
            driver
            for driver in _store().list_driver_presence(organization_id=organization_id, limit=100)
            if str(driver.get("status")) == "online"
        ]
    )
    active_rides = len(
        [
            ride
            for ride in _store().list_rides(organization_id=organization_id, limit=100)
            if ride.get("status") != "completed"
        ]
    )
    return active_rides, active_drivers


def build_driver_intelligence_projection(
    *,
    organization_id: str,
    driver_id: str | None = None,
) -> dict[str, Any]:
    active_rides, active_drivers = _active_counts(organization_id=organization_id)
    demand_level = _demand_level(active_rides, active_drivers)
    trust_score = _latest_trust_score(organization_id=organization_id)
    compliance = _compliance_summary(organization_id=organization_id)
    alerts = _latest_alerts(organization_id=organization_id)
    zone = _latest_zone(organization_id=organization_id)
    predictive_positioning = _predictive_positioning(
        organization_id=organization_id,
        zone=zone,
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
    )
    city_automation = _city_automation_projection(
        organization_id=organization_id,
        zone=zone,
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
        active_rides=active_rides,
    )
    multi_city_orchestration = _multi_city_orchestration_projection(
        organization_id=organization_id,
        zone=zone,
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
        active_rides=active_rides,
    )
    digital_twin_projection = phase0_control_plane.build_dashboard_digital_twin(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    business_pricing = build_business_pricing_projection(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    business_optimization = build_business_budget_allocation_projection(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    demand_forecast = phase0_control_plane.build_dashboard_demand_forecast(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    navigation_intelligence = build_navigation_maps_intelligence_projection(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    phase7_analytics_intelligence = build_phase7_analytics_intelligence_projection(
        organization_id=organization_id,
        source="novaride_mobile_driver_intelligence",
    )
    digital_twin = dict(digital_twin_projection.get("digital_twin", digital_twin_projection))
    self_improving_loop = dict(digital_twin_projection.get("self_improving_loop", {}))
    if demand_level == "high" and not alerts:
        alerts = [f"High demand in {zone}", "Move closer to verified pickup zones"]
    elif demand_level == "moderate" and not alerts:
        alerts = [f"Steady demand in {zone}"]
    return {
        "view": "novaride_mobile_driver_intelligence",
        "organization_id": organization_id,
        "driver_id": driver_id,
        "status": "online" if active_drivers > 0 else "offline",
        "zone": zone,
        "demand_level": demand_level,
        "surge": _surge_multiplier(demand_level),
        "alerts": alerts[:5],
        "compliance": compliance,
        "trust_score": trust_score,
        "predictive_positioning": predictive_positioning,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "digital_twin": digital_twin,
        "self_improving_loop": self_improving_loop,
        "business_pricing": {
            "pricing_posture": business_pricing["pricing"]["pricing_posture"],
            "price_multiplier": business_pricing["pricing"]["price_multiplier"],
            "adjusted_price": business_pricing["pricing"]["adjusted_price"],
            "currency": business_pricing["pricing"]["currency"],
            "incentive_focus": business_pricing["incentives"]["focus"],
            "incentive_plan": business_pricing["incentives"]["plan"],
            "driver_message": business_pricing["incentives"]["driver_message"],
            "rider_message": business_pricing["incentives"]["rider_message"],
            "take_rate": business_pricing["incentives"]["commercial_take_rate"],
            "projection_only": True,
            "read_only": True,
        },
        "business_optimization": {
            "mode": business_optimization["budget_allocation"]["mode"],
            "budget_allocation": business_optimization["budget_allocation"],
            "profit_optimization": business_optimization["profit_optimization"],
            "city_signals": business_optimization["city_signals"],
            "projection_only": True,
            "read_only": True,
        },
        "navigation_intelligence": {
            "route_optimization": navigation_intelligence["route_optimization"],
            "traffic_aware_routing": navigation_intelligence["traffic_aware_routing"],
            "pickup_precision": navigation_intelligence["pickup_precision"],
            "heatmaps": navigation_intelligence["heatmaps"],
            "capital_allocation": navigation_intelligence["capital_allocation"],
            "controlled_execution": navigation_intelligence["controlled_execution"],
            "projection_only": True,
            "read_only": True,
        },
        "analytics_intelligence": {
            "view": phase7_analytics_intelligence["view"],
            "revenue_dashboard": phase7_analytics_intelligence["revenue_dashboard"],
            "driver_performance": phase7_analytics_intelligence["driver_performance"],
            "ride_metrics": phase7_analytics_intelligence["ride_metrics"],
            "demand_forecast": phase7_analytics_intelligence["demand_forecast"],
            "churn_analysis": phase7_analytics_intelligence["churn_analysis"],
            "live_gps_stream": phase7_analytics_intelligence["live_gps_stream"],
            "learning_engine": phase7_analytics_intelligence["learning_engine"],
            "real_time_execution": phase7_analytics_intelligence["real_time_execution"],
            "projection_only": True,
            "read_only": True,
        },
        "demand_forecast": {
            "model": demand_forecast["model"],
            "realtime_analytics": demand_forecast["realtime_analytics"],
            "city_forecasts": demand_forecast["city_forecasts"],
            "forecast_windows": demand_forecast["forecast_windows"],
            "recommendation": demand_forecast["recommendation"],
            "projection_only": True,
            "read_only": True,
        },
        "autonomous_mode": predictive_positioning["mode"] == "fully_autonomous"
        or city_automation["mode"] == "zero_operator"
        or multi_city_orchestration["mode"] == "global_zero_operator",
        "recommendation": multi_city_orchestration["instruction"]
        if multi_city_orchestration["mode"] == "global_zero_operator"
        else city_automation["instruction"]
        if city_automation["mode"] == "zero_operator"
        else predictive_positioning["instruction"],
        "projection_only": True,
        "read_only": True,
        "created_at": _now(),
    }


def build_passenger_intelligence_projection(
    *,
    organization_id: str,
    passenger_id: str | None = None,
) -> dict[str, Any]:
    active_rides, active_drivers = _active_counts(organization_id=organization_id)
    demand_level = _demand_level(active_rides, active_drivers)
    trust_score = _latest_trust_score(organization_id=organization_id)
    alerts = _latest_alerts(organization_id=organization_id)
    predictive_positioning = _predictive_positioning(
        organization_id=organization_id,
        zone=_latest_zone(organization_id=organization_id),
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
    )
    city_automation = _city_automation_projection(
        organization_id=organization_id,
        zone=_latest_zone(organization_id=organization_id),
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
        active_rides=active_rides,
    )
    multi_city_orchestration = _multi_city_orchestration_projection(
        organization_id=organization_id,
        zone=_latest_zone(organization_id=organization_id),
        demand_level=demand_level,
        trust_score=trust_score,
        active_drivers=active_drivers,
        active_rides=active_rides,
    )
    digital_twin_projection = phase0_control_plane.build_dashboard_digital_twin(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    business_pricing = build_business_pricing_projection(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    business_optimization = build_business_budget_allocation_projection(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    demand_forecast = phase0_control_plane.build_dashboard_demand_forecast(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    navigation_intelligence = build_navigation_maps_intelligence_projection(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    phase7_analytics_intelligence = build_phase7_analytics_intelligence_projection(
        organization_id=organization_id,
        source="novaride_mobile_passenger_intelligence",
    )
    digital_twin = dict(digital_twin_projection.get("digital_twin", digital_twin_projection))
    self_improving_loop = dict(digital_twin_projection.get("self_improving_loop", {}))
    if not alerts:
        if demand_level == "high":
            alerts = ["High demand in your area", "Slight delays expected"]
        elif demand_level == "moderate":
            alerts = ["Demand is moderate", "Driver matching remains stable"]
        else:
            alerts = ["System status is stable"]
    return {
        "view": "novaride_mobile_passenger_intelligence",
        "organization_id": organization_id,
        "passenger_id": passenger_id,
        "system_status": "stable",
        "safety_score": min(100, max(80, trust_score + 2)),
        "demand": demand_level,
        "eta_confidence": "high" if active_drivers > 0 else "medium",
        "alerts": alerts[:5],
        "predictive_positioning": predictive_positioning,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city_orchestration,
        "digital_twin": digital_twin,
        "self_improving_loop": self_improving_loop,
        "business_pricing": {
            "pricing_posture": business_pricing["pricing"]["pricing_posture"],
            "price_multiplier": business_pricing["pricing"]["price_multiplier"],
            "adjusted_price": business_pricing["pricing"]["adjusted_price"],
            "currency": business_pricing["pricing"]["currency"],
            "incentive_focus": business_pricing["incentives"]["focus"],
            "incentive_plan": business_pricing["incentives"]["plan"],
            "driver_message": business_pricing["incentives"]["driver_message"],
            "rider_message": business_pricing["incentives"]["rider_message"],
            "take_rate": business_pricing["incentives"]["commercial_take_rate"],
            "projection_only": True,
            "read_only": True,
        },
        "business_optimization": {
            "mode": business_optimization["budget_allocation"]["mode"],
            "budget_allocation": business_optimization["budget_allocation"],
            "profit_optimization": business_optimization["profit_optimization"],
            "city_signals": business_optimization["city_signals"],
            "projection_only": True,
            "read_only": True,
        },
        "navigation_intelligence": {
            "route_optimization": navigation_intelligence["route_optimization"],
            "traffic_aware_routing": navigation_intelligence["traffic_aware_routing"],
            "pickup_precision": navigation_intelligence["pickup_precision"],
            "heatmaps": navigation_intelligence["heatmaps"],
            "capital_allocation": navigation_intelligence["capital_allocation"],
            "controlled_execution": navigation_intelligence["controlled_execution"],
            "projection_only": True,
            "read_only": True,
        },
        "analytics_intelligence": {
            "view": phase7_analytics_intelligence["view"],
            "revenue_dashboard": phase7_analytics_intelligence["revenue_dashboard"],
            "driver_performance": phase7_analytics_intelligence["driver_performance"],
            "ride_metrics": phase7_analytics_intelligence["ride_metrics"],
            "demand_forecast": phase7_analytics_intelligence["demand_forecast"],
            "churn_analysis": phase7_analytics_intelligence["churn_analysis"],
            "live_gps_stream": phase7_analytics_intelligence["live_gps_stream"],
            "learning_engine": phase7_analytics_intelligence["learning_engine"],
            "real_time_execution": phase7_analytics_intelligence["real_time_execution"],
            "projection_only": True,
            "read_only": True,
        },
        "demand_forecast": {
            "model": demand_forecast["model"],
            "realtime_analytics": demand_forecast["realtime_analytics"],
            "city_forecasts": demand_forecast["city_forecasts"],
            "forecast_windows": demand_forecast["forecast_windows"],
            "recommendation": demand_forecast["recommendation"],
            "projection_only": True,
            "read_only": True,
        },
        "autonomous_mode": predictive_positioning["mode"] == "fully_autonomous"
        or city_automation["mode"] == "zero_operator"
        or multi_city_orchestration["mode"] == "global_zero_operator",
        "trust": {
            "driver_verified": trust_score >= 90,
            "vehicle_verified": trust_score >= 88,
            "payment_secure": True,
        },
        "projection_only": True,
        "read_only": True,
        "created_at": _now(),
    }


__all__ = [
    "build_driver_intelligence_projection",
    "build_passenger_intelligence_projection",
]
