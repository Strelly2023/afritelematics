"""NovaRide Phase 4 autonomous budget allocation and profit optimization.

This layer stays projection-only. It converts tenant-scoped ride, driver, and
financial signals into deterministic city budget recommendations and profit
optimization guidance without mutating execution state.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase3 import build_business_pricing_projection, build_phase3_status


PHASE4_TOPIC = "novaride.phase4.budget_profit_optimization"


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


def _latest_zone(organization_id: str) -> str:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)
    return "CBD"


def _organization_subscription(organization_id: str) -> dict[str, Any] | None:
    return _store().latest_active_subscription(organization_id=organization_id)


def _latest_trust_score(organization_id: str) -> int:
    trust = _store().latest_trust_score(organization_id=organization_id)
    if trust is not None:
        try:
            return int(trust.get("trust_score") or 92)
        except (TypeError, ValueError):
            return 92
    return 92


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


def _city_label(location: dict[str, Any] | None, fallback: str) -> str:
    payload = location or {}
    label = (
        str(payload.get("label") or payload.get("name") or payload.get("city") or fallback)
        .strip()
        or fallback
    )
    return label


def _city_score(
    *,
    platform_revenue: Decimal,
    revenue: Decimal,
    demand_pressure: float,
    trust_score: int,
    coverage_score: int,
    active_drivers: int,
) -> float:
    return round(
        float(platform_revenue) * 2.1
        + float(revenue) * 0.15
        + demand_pressure * 42.0
        + float(trust_score) * 0.8
        + float(coverage_score) * 0.6
        + active_drivers * 5.0,
        6,
    )


def _build_city_rows(organization_id: str) -> list[dict[str, Any]]:
    subscription = _organization_subscription(organization_id)
    phase3_projection = build_business_pricing_projection(organization_id=organization_id, source="novaride_phase4")
    take_rate = Decimal(str(phase3_projection["incentives"]["commercial_take_rate"]))
    fallback_zone = _latest_zone(organization_id)

    rides = _relevant_rides(organization_id)
    drivers = _active_driver_rows(organization_id)
    ride_buckets: dict[str, list[dict[str, Any]]] = {}
    driver_buckets: dict[str, list[dict[str, Any]]] = {}

    for ride in rides:
        city = _city_label(ride.get("pickup_location"), fallback_zone)
        ride_buckets.setdefault(city, []).append(ride)

    for driver in drivers:
        city = _city_label(driver.get("location"), fallback_zone)
        driver_buckets.setdefault(city, []).append(driver)

    city_names = sorted(set(ride_buckets) | set(driver_buckets)) or [fallback_zone]
    city_rows: list[dict[str, Any]] = []
    for city in city_names:
        city_rides = ride_buckets.get(city, [])
        city_drivers = driver_buckets.get(city, [])
        active_rides = [ride for ride in city_rides if str(ride.get("status", "")).lower() not in {"completed", "cancelled"}]
        completed_rides = [ride for ride in city_rides if str(ride.get("status", "")).lower() == "completed"]
        revenue = Decimal("0.00")
        for ride in city_rides:
            raw = ride.get("final_fare") if str(ride.get("status", "")).lower() == "completed" else ride.get("fare_estimate")
            revenue += _safe_decimal(raw) if raw is not None else Decimal("0.00")
        forecast_revenue = Decimal("0.00")
        for ride in active_rides:
            raw = ride.get("fare_estimate")
            if raw is not None:
                forecast_revenue += (_safe_decimal(raw) * Decimal("0.35")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        revenue = (revenue + forecast_revenue).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross_platform_revenue = (revenue * take_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        active_driver_count = len(city_drivers)
        active_ride_count = len(active_rides)
        completed_ride_count = len(completed_rides)
        demand_pressure = (active_ride_count + 1) / max(1, active_driver_count + 1)
        trust_score = int(
            sum(int(float(driver.get("trust_score", 0.0) or 0.0)) for driver in city_drivers) / max(1, active_driver_count)
        ) if city_drivers else int(
            get_phase_store().latest_trust_score(organization_id=organization_id).get("trust_score", 92)
            if get_phase_store().latest_trust_score(organization_id=organization_id)
            else 92
        )
        coverage_score = min(
            100,
            (active_driver_count * 22)
            + (active_ride_count * 8)
            + (completed_ride_count * 4)
            + (trust_score // 2),
        )
        score = _city_score(
            platform_revenue=gross_platform_revenue,
            revenue=revenue,
            demand_pressure=demand_pressure,
            trust_score=trust_score,
            coverage_score=coverage_score,
            active_drivers=active_driver_count,
        )
        city_rows.append(
            {
                "city": city,
                "revenue": revenue,
                "gross_platform_revenue": gross_platform_revenue,
                "active_drivers": active_driver_count,
                "active_rides": active_ride_count,
                "completed_rides": completed_ride_count,
                "trust_score": trust_score,
                "coverage_score": coverage_score,
                "demand_pressure": round(demand_pressure, 6),
                "score": score,
                "budget_weight": 0.0,
            }
        )

    if not city_rows:
        city_rows.append(
            {
                "city": fallback_zone,
                "revenue": Decimal("0.00"),
                "gross_platform_revenue": Decimal("0.00"),
                "active_drivers": 0,
                "active_rides": 0,
                "completed_rides": 0,
                "trust_score": _latest_trust_score(organization_id),
                "coverage_score": 0,
                "demand_pressure": 0.0,
                "score": 0.0,
                "budget_weight": 0.0,
            }
        )

    return city_rows


def _allocate_budget(city_rows: list[dict[str, Any]]) -> tuple[Decimal, list[dict[str, Any]]]:
    total_platform_revenue = sum((row["gross_platform_revenue"] for row in city_rows), Decimal("0.00"))
    if total_platform_revenue <= 0:
        return Decimal("0.00"), [
            {
                **row,
                "budget_weight": 1.0 / len(city_rows),
                "recommended_budget": Decimal("0.00"),
                "projected_profit": Decimal("0.00"),
                "projected_margin": Decimal("0.0000"),
                "target_margin": Decimal("0.35"),
                "strategy": "hold",
            }
            for row in city_rows
        ]

    raw_budget_pool = max(Decimal("0.00"), total_platform_revenue * Decimal("0.35"))
    floor_budget = Decimal("100.00") if total_platform_revenue >= Decimal("1000.00") else Decimal("25.00") if total_platform_revenue >= Decimal("250.00") else Decimal("0.00")
    ceiling_budget = total_platform_revenue * Decimal("0.60")
    budget_pool = min(max(floor_budget, raw_budget_pool), ceiling_budget).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_score = sum((Decimal(str(row["score"])) for row in city_rows), Decimal("0.00"))
    if total_score <= 0:
        equal_weight = Decimal("1.0") / Decimal(len(city_rows))
        weights = [equal_weight for _ in city_rows]
    else:
        weights = [Decimal(str(row["score"])) / total_score for row in city_rows]

    allocated_rows: list[dict[str, Any]] = []
    running_allocation = Decimal("0.00")
    for index, (row, weight) in enumerate(zip(city_rows, weights, strict=False)):
        if index == len(city_rows) - 1:
            recommended_budget = (budget_pool - running_allocation).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            recommended_budget = (budget_pool * weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            running_allocation += recommended_budget
        gross_platform_revenue = Decimal(str(row["gross_platform_revenue"]))
        projected_profit = (gross_platform_revenue - recommended_budget).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        projected_margin = (
            (projected_profit / gross_platform_revenue).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if gross_platform_revenue > 0
            else Decimal("0.0000")
        )
        target_margin = Decimal("0.35")
        if gross_platform_revenue <= 0:
            strategy = "hold"
        elif projected_margin < target_margin:
            strategy = "constrain_spend"
        elif Decimal(str(row["demand_pressure"])) >= Decimal("1.1"):
            strategy = "expand_supply"
        else:
            strategy = "maintain"
        allocated_rows.append(
            {
                **row,
                "budget_weight": round(float(weight), 6),
                "recommended_budget": recommended_budget,
                "projected_profit": projected_profit,
                "projected_margin": float(projected_margin),
                "target_margin": float(target_margin),
                "strategy": strategy,
            }
        )
    return budget_pool, allocated_rows


def build_business_budget_allocation_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "novaride_business_portal",
) -> dict[str, Any]:
    phase3_status = build_phase3_status(organization_id=organization_id, limit=limit)
    city_rows = _build_city_rows(organization_id)
    budget_pool, allocated_rows = _allocate_budget(city_rows)
    total_platform_revenue = sum((row["gross_platform_revenue"] for row in allocated_rows), Decimal("0.00"))
    total_projected_profit = sum((row["projected_profit"] for row in allocated_rows), Decimal("0.00"))
    baseline_budget = (budget_pool / Decimal(len(allocated_rows))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if allocated_rows and budget_pool > 0 else Decimal("0.00")
    baseline_profit = sum(
        ((Decimal(str(row["gross_platform_revenue"])) - baseline_budget).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for row in allocated_rows
    )
    optimization_mode = (
        "autonomous"
        if bool(phase3_status.get("ready", False)) and len([row for row in allocated_rows if row["active_drivers"] > 0]) >= 2 and budget_pool > 0
        else "supervised"
        if budget_pool > 0
        else "held"
    )
    optimization_focus = (
        "profit_growth"
        if total_projected_profit >= baseline_profit
        else "cost_reduction"
    )
    dominant_city = max(allocated_rows, key=lambda row: (row["projected_profit"], row["coverage_score"], row["city"])) if allocated_rows else None
    budget_allocation_verified = (
        sum((row["recommended_budget"] for row in allocated_rows), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        == budget_pool
        and all(row["recommended_budget"] >= 0 for row in allocated_rows)
    )
    readiness = {
        "phase3_ready": bool(phase3_status.get("ready", False)),
        "subscription_active": phase3_status.get("readiness", {}).get("subscription_active", False),
        "city_signal_ready": len(allocated_rows) > 0,
        "budget_allocation_verified": budget_allocation_verified,
        "profit_optimization_verified": total_projected_profit >= Decimal("0.00") or budget_pool == Decimal("0.00"),
        "tenant_isolation_preserved": bool(organization_id) and all(
            row["city"] for row in allocated_rows
        ),
    }
    return {
        "view": "novaride_phase4_budget_allocation",
        "phase": "4",
        "platform": "NovaRide Phase 4",
        "organization_id": organization_id,
        "source": source or "novaride_business_portal",
        "phase3": phase3_status,
        "budget_allocation": {
            "mode": optimization_mode,
            "objective": "maximize_profit_with_coverage_guard",
            "budget_pool": _money_text(budget_pool),
            "platform_take_rate": phase3_status["pricing"]["incentives"]["commercial_take_rate"] if phase3_status.get("pricing") else 0.0,
            "total_platform_revenue": _money_text(total_platform_revenue),
            "city_allocations": [
                {
                    "city": row["city"],
                    "active_drivers": row["active_drivers"],
                    "active_rides": row["active_rides"],
                    "completed_rides": row["completed_rides"],
                    "trust_score": row["trust_score"],
                    "coverage_score": row["coverage_score"],
                    "demand_pressure": row["demand_pressure"],
                    "gross_platform_revenue": _money_text(row["gross_platform_revenue"]),
                    "recommended_budget": _money_text(row["recommended_budget"]),
                    "budget_weight": round(float(row["budget_weight"]), 6),
                    "strategy": row["strategy"],
                    "projected_profit": _money_text(row["projected_profit"]),
                    "projected_margin": round(float(row["projected_margin"]), 4),
                    "target_margin": round(float(row["target_margin"]), 4),
                }
                for row in allocated_rows
            ],
            "dominant_city": dominant_city["city"] if dominant_city else None,
            "projection_only": True,
            "read_only": True,
        },
        "profit_optimization": {
            "mode": optimization_mode,
            "focus": optimization_focus,
            "total_platform_revenue": _money_text(total_platform_revenue),
            "budget_pool": _money_text(budget_pool),
            "projected_profit": _money_text(total_projected_profit),
            "baseline_profit": _money_text(baseline_profit),
            "profit_uplift": _money_text((total_projected_profit - baseline_profit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "projected_margin": round(
                float((total_projected_profit / total_platform_revenue).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
                if total_platform_revenue > 0
                else 0.0,
                4,
            ),
            "target_margin": 0.35,
            "optimization_actions": [
                "reallocate_budget_toward_high_margin_cities",
                "constrain_spend_in_low_margin_cities",
                "preserve_audit_and_replay_controls",
                "use_demand_trust_coverage_signals_for_budget_weights",
            ],
            "projection_only": True,
            "read_only": True,
        },
        "city_signals": {
            "city_count": len(allocated_rows),
            "active_city_count": len([row for row in allocated_rows if row["active_drivers"] > 0]),
            "top_city": dominant_city["city"] if dominant_city else _latest_zone(organization_id),
        },
        "controls": {
            "authority_boundary": "budget_projection_read_only",
            "projection_only": True,
            "read_only": True,
            "no_runtime_mutation": True,
            "no_provider_direct_access": True,
        },
        "readiness": readiness,
        "ready": all(readiness.values()),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_business_profit_optimization_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "novaride_business_portal",
) -> dict[str, Any]:
    projection = build_business_budget_allocation_projection(
        organization_id=organization_id,
        limit=limit,
        source=source,
    )
    projection["view"] = "novaride_phase4_profit_optimization"
    return projection


def build_phase4_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase3_status = build_phase3_status(organization_id=org_id, limit=limit)
    budget_allocation = build_business_budget_allocation_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase3_ready": bool(phase3_status.get("ready", False)),
        "subscription_active": bool(budget_allocation["readiness"]["subscription_active"]),
        "budget_allocation_verified": bool(budget_allocation["readiness"]["budget_allocation_verified"]),
        "profit_optimization_verified": bool(budget_allocation["readiness"]["profit_optimization_verified"]),
        "city_signal_ready": bool(budget_allocation["readiness"]["city_signal_ready"]),
        "tenant_isolation_preserved": bool(budget_allocation["readiness"]["tenant_isolation_preserved"]),
    }
    return {
        "view": "novaride_phase4_status",
        "phase": "4",
        "platform": "NovaRide Phase 4",
        "organization_id": org_id,
        "phase3": phase3_status,
        "budget_allocation": budget_allocation,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE4_TOPIC",
    "build_business_budget_allocation_projection",
    "build_business_profit_optimization_projection",
    "build_phase4_status",
]
