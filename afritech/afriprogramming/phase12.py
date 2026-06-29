"""NovaRide Phase 12 global scaling system.

This layer remains projection-only. It composes the existing autonomy,
pricing, demand, compliance, and outcome learning surfaces into a bounded
global scaling view for multi-city management, geo-fencing, currency support,
localization, region pricing, distributed infrastructure, fraud prediction,
and driver incentives optimization without creating execution authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase11 import build_phase11_compliance_workspace_projection


PHASE12_TOPIC = "novaride.phase12.multi_city_global_scaling"

NOVARIDE_PHASE12_MODULES = (
    {
        "key": "multi_city_management",
        "name": "Multi-City Management",
        "purpose": "Coordinate city coverage, orchestration, and supply balancing across tenant-scoped markets.",
    },
    {
        "key": "geo_fencing",
        "name": "Geo-Fencing",
        "purpose": "Bound service zones, restricted areas, airport rules, and city-level operating surfaces.",
    },
    {
        "key": "currency_support",
        "name": "Currency Support",
        "purpose": "Project currency coverage and settlement surfaces for multi-market operations.",
    },
    {
        "key": "localization",
        "name": "Localization",
        "purpose": "Surface language and locale readiness for regional rollouts.",
    },
    {
        "key": "region_based_pricing",
        "name": "Region-Based Pricing",
        "purpose": "Project localized pricing and bounded take-rate posture per city and region.",
    },
    {
        "key": "distributed_infrastructure",
        "name": "Distributed Infrastructure",
        "purpose": "Describe the regional deployment and replication posture for global rollout.",
    },
    {
        "key": "auto_decision_engine",
        "name": "Auto Decision Engine",
        "purpose": "Combine multi-city, demand, trust, and compliance signals into bounded scale recommendations.",
    },
    {
        "key": "fraud_prediction_models",
        "name": "Fraud Prediction Models",
        "purpose": "Predict city and global fraud pressure using compliance, support, and trust signals.",
    },
    {
        "key": "driver_incentives_optimization",
        "name": "Driver Incentives Optimization",
        "purpose": "Recommend bounded driver incentives from demand, supply, and regional pressure surfaces.",
    },
    {
        "key": "global_learning",
        "name": "Global Learning",
        "purpose": "Project the learning loop that keeps multi-city rollouts adaptive while staying review-bound.",
    },
)

NOVARIDE_PHASE12_NAVIGATION = (
    "workspace",
    "multi_city",
    "geo_fencing",
    "currency_support",
    "localization",
    "region_pricing",
    "distributed_infrastructure",
    "auto_decision_engine",
    "fraud_prediction",
    "driver_incentives",
    "global_learning",
)

NOVARIDE_PHASE12_ALLOWED_ACTIONS = (
    "view_global_scaling_dashboard",
    "review_city_orchestration",
    "review_geo_fences",
    "review_currency_support",
    "review_localization",
    "review_region_pricing",
    "review_distribution_plan",
    "review_decision_engine",
    "review_fraud_predictions",
    "review_driver_incentives",
)

NOVARIDE_PHASE12_FORBIDDEN_ACTIONS = (
    "direct_provider_access",
    "direct_payment_execution",
    "override_trust_engine",
    "bypass_audit_chain",
)


def _store():
    return get_phase_store()


def _now() -> str:
    return phase_now()


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - defensive
        return Decimal(default)


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


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _city_label(location: dict[str, Any] | None) -> str:
    if not isinstance(location, dict):
        return "CBD"
    for key in ("label", "city", "name", "zone", "region"):
        label = _normalize_text(location.get(key))
        if label:
            return label
    return "CBD"


def _latest_snapshot_payload(organization_id: str) -> dict[str, Any]:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    payload = snapshot.get("payload", {}) if snapshot else {}
    return payload if isinstance(payload, dict) else {}


def _snapshot_region_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    for key in ("market_regions", "city_regions", "regions", "global_regions"):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            regions.extend(item for item in candidate if isinstance(item, dict))
    index: dict[str, dict[str, Any]] = {}
    for region in regions:
        city = _normalize_text(region.get("city") or region.get("label") or region.get("name")).lower()
        if city:
            index[city] = region
    return index


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _city_topology(organization_id: str, limit: int) -> list[dict[str, Any]]:
    payload = _latest_snapshot_payload(organization_id)
    region_index = _snapshot_region_index(payload)
    driver_presence = _store().list_driver_presence(organization_id=organization_id, limit=limit)
    rides = _store().list_rides(organization_id=organization_id, limit=limit)
    trust = _store().latest_trust_score(organization_id=organization_id)
    trust_score = _safe_int(trust.get("trust_score"), 90) if trust else 90

    city_map: dict[str, dict[str, Any]] = {}

    for presence in driver_presence:
        location = presence.get("location") or {}
        city = _city_label(location)
        bucket = city_map.setdefault(
            city,
            {
                "city": city,
                "country_code": None,
                "currency": None,
                "language": None,
                "geo_fence": None,
                "region_price_multiplier": 1.0,
                "drivers": 0,
                "rides": 0,
                "completed_rides": 0,
                "active_rides": 0,
                "trust_total": 0,
                "currencies": set(),
                "languages": set(),
                "country_codes": set(),
                "zone_ids": set(),
            },
        )
        bucket["drivers"] += 1
        bucket["trust_total"] += _safe_int(presence.get("trust_score"), trust_score)
        metadata = presence.get("metadata") if isinstance(presence.get("metadata"), dict) else {}
        region = region_index.get(city.lower(), {})
        country_code = _normalize_text(
            region.get("country_code") or metadata.get("country_code") or location.get("country_code"),
            default="AU",
        ).upper()
        currency = _normalize_text(
            region.get("currency") or metadata.get("currency") or location.get("currency"),
            default="AUD",
        ).upper()
        language = _normalize_text(
            region.get("language") or metadata.get("language") or location.get("language"),
            default="en",
        ).lower()
        geo_fence = _normalize_text(
            region.get("geo_fence") or metadata.get("geo_fence") or f"{country_code}-{city.replace(' ', '-').upper()}",
            default=f"{country_code}-{city.replace(' ', '-').upper()}",
        )
        bucket["country_code"] = country_code
        bucket["currency"] = currency
        bucket["language"] = language
        bucket["geo_fence"] = geo_fence
        bucket["region_price_multiplier"] = _safe_float(
            region.get("region_price_multiplier") or metadata.get("region_price_multiplier"),
            1.0,
        )
        bucket["currencies"].add(currency)
        bucket["languages"].add(language)
        bucket["country_codes"].add(country_code)
        bucket["zone_ids"].add(geo_fence)

    for ride in rides:
        pickup = ride.get("pickup_location") or {}
        city = _city_label(pickup)
        bucket = city_map.setdefault(
            city,
            {
                "city": city,
                "country_code": None,
                "currency": None,
                "language": None,
                "geo_fence": None,
                "region_price_multiplier": 1.0,
                "drivers": 0,
                "rides": 0,
                "completed_rides": 0,
                "active_rides": 0,
                "trust_total": 0,
                "currencies": set(),
                "languages": set(),
                "country_codes": set(),
                "zone_ids": set(),
            },
        )
        bucket["rides"] += 1
        if str(ride.get("status", "")).lower() == "completed":
            bucket["completed_rides"] += 1
        else:
            bucket["active_rides"] += 1
        currency = _normalize_text(ride.get("currency") or payload.get("default_currency"), default="AUD").upper()
        bucket["currencies"].add(currency)

    cities: list[dict[str, Any]] = []
    for city in sorted(city_map.values(), key=lambda item: (-int(item["drivers"]), -int(item["rides"]), item["city"])):
        drivers_count = int(city["drivers"])
        rides_count = int(city["rides"])
        average_trust = int(city["trust_total"] / drivers_count) if drivers_count else trust_score
        coverage_score = min(100, (drivers_count * 22) + (rides_count * 4) + (average_trust // 2))
        demand_index = min(100, rides_count * 18 + max(0, rides_count - drivers_count) * 12 + (100 - average_trust) // 4)
        supply_gap = max(0, rides_count - drivers_count)
        mode = (
            "zero_operator"
            if drivers_count >= 3 and coverage_score >= 75
            else "city_autonomous"
            if drivers_count >= 2 and coverage_score >= 60
            else "city_supervised"
            if drivers_count > 0
            else "city_held"
        )
        if city.get("currency") is None:
            city["currency"] = sorted(city["currencies"])[0] if city["currencies"] else "AUD"
        if city.get("country_code") is None:
            city["country_code"] = sorted(city["country_codes"])[0] if city["country_codes"] else "AU"
        if city.get("language") is None:
            city["language"] = sorted(city["languages"])[0] if city["languages"] else "en"
        cities.append(
            {
                "city": city["city"],
                "country_code": city["country_code"],
                "currency": city["currency"],
                "language": city["language"],
                "geo_fence": city["geo_fence"] or f'{city["country_code"]}-{city["city"].replace(" ", "-").upper()}',
                "region_price_multiplier": round(city["region_price_multiplier"], 4),
                "drivers": drivers_count,
                "rides": rides_count,
                "completed_rides": int(city["completed_rides"]),
                "active_rides": int(city["active_rides"]),
                "average_trust_score": average_trust,
                "coverage_score": coverage_score,
                "demand_index": demand_index,
                "supply_gap": supply_gap,
                "mode": mode,
                "currencies": sorted(city["currencies"]) or ["AUD"],
                "languages": sorted(city["languages"]) or ["en"],
            }
        )

    if not cities:
        fallback_currency = _normalize_text(payload.get("default_currency") or "AUD", default="AUD").upper()
        fallback_language = _normalize_text(payload.get("default_language") or "en", default="en").lower()
        fallback_city = _normalize_text(payload.get("primary_city") or payload.get("primary_zone") or "CBD")
        cities = [
            {
                "city": fallback_city,
                "country_code": _normalize_text(payload.get("primary_country_code") or "AU", default="AU").upper(),
                "currency": fallback_currency,
                "language": fallback_language,
                "geo_fence": _normalize_text(payload.get("primary_geo_fence") or f'AU-{fallback_city.replace(" ", "-").upper()}'),
                "region_price_multiplier": 1.0,
                "drivers": 0,
                "rides": 0,
                "completed_rides": 0,
                "active_rides": 0,
                "average_trust_score": trust_score,
                "coverage_score": min(100, trust_score // 2),
                "demand_index": 0,
                "supply_gap": 0,
                "mode": "city_held",
                "currencies": [fallback_currency],
                "languages": [fallback_language],
            }
        ]

    return cities


def _business_pricing_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_business_pricing", organization_id=organization_id, limit=limit)


def _city_profit_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_city_profit_optimization", organization_id=organization_id, limit=limit)


def _demand_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_demand_forecast", organization_id=organization_id, limit=limit)


def _autonomy_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_autonomy", organization_id=organization_id, limit=limit)


def _city_automation_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_city_automation", organization_id=organization_id, limit=limit)


def _multi_city_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_multi_city_orchestration", organization_id=organization_id, limit=limit)


def _digital_twin_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_digital_twin", organization_id=organization_id, limit=limit)


def _meta_learning_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_dashboard_meta_learning_redesign", organization_id=organization_id, limit=limit)


def _outcome_learning_projection(organization_id: str, limit: int) -> dict[str, Any]:
    return build_control_projection("build_outcome_learning", organization_id=organization_id, limit=limit)


def _phase12_multi_city_management_projection(
    *,
    organization_id: str,
    phase11: dict[str, Any],
    autonomy: dict[str, Any],
    city_automation: dict[str, Any],
    multi_city: dict[str, Any],
    digital_twin: dict[str, Any],
    demand_forecast: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    cities = _city_topology(organization_id, limit)
    active_city_count = len([city for city in cities if city["drivers"] > 0])
    city_count = len(cities)
    global_coverage = round(sum(city["coverage_score"] for city in cities) / max(1, city_count), 2)
    global_trust = round(sum(city["average_trust_score"] for city in cities) / max(1, city_count), 2)
    global_demand = max(city["demand_index"] for city in cities)
    supported_currencies = sorted({currency for city in cities for currency in city["currencies"]})
    supported_languages = sorted({language for city in cities for language in city["languages"]})
    primary_city = cities[0]["city"]
    mode = (
        "global_zero_operator"
        if active_city_count >= 2 and global_coverage >= 75 and phase11["ready"] and fraud_prediction_ready(phase11)
        else "global_autonomous"
        if active_city_count >= 2 and global_coverage >= 60
        else "global_supervised"
        if active_city_count > 0
        else "global_held"
    )
    instruction = (
        "Keep multi-city orchestration active and rebalance supply toward the highest coverage cities"
        if mode == "global_zero_operator"
        else "Autonomously rebalance supply across cities"
        if mode == "global_autonomous"
        else "Hold supervised orchestration across active cities"
        if mode == "global_supervised"
        else "Hold orchestration until additional cities come online"
    )
    reason = (
        "Global coverage, trust, and compliance support zero-operator orchestration"
        if mode == "global_zero_operator"
        else "Multi-city supply is healthy enough for autonomous orchestration"
        if mode == "global_autonomous"
        else "Orchestration is available but still requires oversight"
        if mode == "global_supervised"
        else "No active multi-city supply is available"
    )
    return {
        "view": "novaride_phase12_multi_city_management",
        "mode": mode,
        "city_count": city_count,
        "active_city_count": active_city_count,
        "primary_city": primary_city,
        "city_topology": cities[:limit],
        "global_coverage_score": global_coverage,
        "global_trust_score": global_trust,
        "global_demand_index": global_demand,
        "supported_currencies": supported_currencies,
        "supported_languages": supported_languages,
        "multi_city_ready": bool(active_city_count >= 2 and global_coverage >= 60 and phase11["ready"]),
        "instruction": instruction,
        "reason": reason,
        "autonomy": autonomy,
        "city_automation": city_automation,
        "multi_city_orchestration": multi_city,
        "digital_twin": digital_twin,
        "demand_forecast": demand_forecast,
        "projection_only": True,
        "read_only": True,
    }


def fraud_prediction_ready(phase11: dict[str, Any]) -> bool:
    fraud = phase11.get("fraud_detection", {})
    return str(fraud.get("risk_band", "low")).lower() in {"low", "watch"}


def _phase12_geo_fencing_projection(
    *,
    organization_id: str,
    multi_city_management: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    geofences = []
    for city in multi_city_management["city_topology"]:
        geofences.append(
            {
                "geo_fence_id": f"geo-{city['city'].replace(' ', '-').lower()}",
                "city": city["city"],
                "country_code": city["country_code"],
                "currency": city["currency"],
                "language": city["language"],
                "status": "active" if city["drivers"] > 0 else "standby",
                "restricted_zones": [],
                "allowed_zones": [city["geo_fence"]],
                "region_price_multiplier": city["region_price_multiplier"],
            }
        )
    ready = bool(geofences) and any(item["status"] == "active" for item in geofences)
    return {
        "view": "novaride_phase12_geo_fencing",
        "geo_fences": geofences[:limit],
        "geo_fence_total": len(geofences),
        "geo_fence_ready": ready,
        "projection_only": True,
        "read_only": True,
    }


def _phase12_currency_support_projection(
    *,
    multi_city_management: dict[str, Any],
    business_pricing: dict[str, Any],
) -> dict[str, Any]:
    supported_currencies = sorted(set(multi_city_management["supported_currencies"]))
    base_currency_source = business_pricing.get("pricing", {}).get("currency") or (
        supported_currencies[0] if supported_currencies else "AUD"
    )
    base_currency = _normalize_text(base_currency_source, default="AUD").upper()
    currency_rows = []
    for city in multi_city_management["city_topology"]:
        currency_rows.append(
            {
                "city": city["city"],
                "currency": city["currency"],
                "base_currency": base_currency,
                "settlement_mode": "local_settlement" if city["currency"] == base_currency else "regional_settlement",
                "supported": city["currency"] in supported_currencies,
            }
        )
    return {
        "view": "novaride_phase12_currency_support",
        "base_currency": base_currency,
        "supported_currencies": supported_currencies,
        "currency_rows": currency_rows,
        "currency_count": len(supported_currencies),
        "currency_support_ready": bool(supported_currencies),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_localization_projection(
    *,
    multi_city_management: dict[str, Any],
) -> dict[str, Any]:
    supported_languages = sorted(set(multi_city_management["supported_languages"]))
    localization_rows = []
    for city in multi_city_management["city_topology"]:
        localization_rows.append(
            {
                "city": city["city"],
                "language": city["language"],
                "locale": f"{city['language']}-{city['country_code']}",
                "direction": "ltr",
                "supported": city["language"] in supported_languages,
            }
        )
    return {
        "view": "novaride_phase12_localization",
        "default_language": supported_languages[0] if supported_languages else "en",
        "supported_languages": supported_languages or ["en"],
        "locales": localization_rows,
        "localization_ready": bool(localization_rows),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_region_pricing_projection(
    *,
    multi_city_management: dict[str, Any],
    business_pricing: dict[str, Any],
) -> dict[str, Any]:
    pricing = business_pricing.get("pricing", {})
    incentives = business_pricing.get("incentives", {})
    base_price = _safe_decimal(pricing.get("adjusted_price") or pricing.get("base_price") or "0")
    region_prices = []
    for city in multi_city_management["city_topology"]:
        multiplier = _safe_float(city.get("region_price_multiplier"), 1.0)
        region_price = (base_price * Decimal(str(multiplier))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        region_prices.append(
            {
                "city": city["city"],
                "country_code": city["country_code"],
                "currency": city["currency"],
                "base_price": _money_text(base_price),
                "region_price_multiplier": round(multiplier, 4),
                "regional_price": _money_text(region_price),
                "commercial_take_rate": incentives.get("commercial_take_rate", 0.0),
            }
        )
    return {
        "view": "novaride_phase12_region_pricing",
        "base_currency": pricing.get("currency", multi_city_management["supported_currencies"][0] if multi_city_management["supported_currencies"] else "AUD"),
        "pricing_posture": pricing.get("pricing_posture", "balanced"),
        "region_prices": region_prices,
        "region_count": len(region_prices),
        "region_pricing_ready": bool(region_prices),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_distributed_infrastructure_projection(
    *,
    multi_city_management: dict[str, Any],
) -> dict[str, Any]:
    regions = []
    for index, city in enumerate(multi_city_management["city_topology"], start=1):
        regions.append(
            {
                "region_id": f"region-{index:02d}",
                "city": city["city"],
                "country_code": city["country_code"],
                "edge_node": f"edge-{city['city'].replace(' ', '-').lower()}",
                "replica_state": "primary" if index == 1 else "replica",
                "deployment_mode": "multi_region_active" if multi_city_management["active_city_count"] >= 2 else "single_region",
                "replication_target_ms": 250 if multi_city_management["active_city_count"] >= 2 else 500,
                "status": "ready" if city["drivers"] > 0 else "standby",
            }
        )
    return {
        "view": "novaride_phase12_distributed_infrastructure",
        "primary_region": regions[0]["city"] if regions else "CBD",
        "deployment_mode": "multi_region_active" if multi_city_management["active_city_count"] >= 2 else "single_region",
        "regions": regions,
        "region_count": len(regions),
        "distributed_ready": bool(regions) and multi_city_management["active_city_count"] >= 2,
        "projection_only": True,
        "read_only": True,
    }


def _phase12_fraud_prediction_projection(
    *,
    organization_id: str,
    phase11: dict[str, Any],
    multi_city_management: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    fraud = phase11.get("fraud_detection", {})
    support = phase11.get("support_dashboard", {})
    base_score = _safe_int(fraud.get("risk_score"), 10)
    support_pressure = _safe_int(support.get("support_pressure"), 0)
    city_risk_profiles = []
    for city in multi_city_management["city_topology"]:
        city_risk = int(
            round(
                _clamp(
                    base_score
                    + max(0, city["supply_gap"] * 8)
                    + max(0, 70 - city["average_trust_score"]) // 2
                    + max(0, city["demand_index"] - 50) // 4
                    + support_pressure,
                    minimum=0.0,
                    maximum=100.0,
                )
            )
        )
        risk_band = "critical" if city_risk >= 80 else "high" if city_risk >= 55 else "watch" if city_risk >= 30 else "low"
        city_risk_profiles.append(
            {
                "city": city["city"],
                "country_code": city["country_code"],
                "risk_score": city_risk,
                "risk_band": risk_band,
                "drivers": city["drivers"],
                "rides": city["rides"],
                "supply_gap": city["supply_gap"],
                "trust_score": city["average_trust_score"],
            }
        )
    predicted_risk_score = int(round(sum(item["risk_score"] for item in city_risk_profiles) / max(1, len(city_risk_profiles))))
    if predicted_risk_score >= 80:
        risk_band = "critical"
    elif predicted_risk_score >= 55:
        risk_band = "high"
    elif predicted_risk_score >= 30:
        risk_band = "watch"
    else:
        risk_band = "low"
    signals = [
        f"phase11 risk: {fraud.get('risk_band', 'low')}",
        f"support pressure: {support_pressure}",
        f"city count: {multi_city_management['city_count']}",
        f"active cities: {multi_city_management['active_city_count']}",
    ]
    return {
        "view": "novaride_phase12_fraud_prediction",
        "model_name": "bounded_global_fraud_predictor",
        "predicted_risk_score": predicted_risk_score,
        "risk_band": risk_band,
        "city_risk_profiles": city_risk_profiles[:limit],
        "predictive_signals": signals,
        "prediction_ready": bool(city_risk_profiles),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_driver_incentives_projection(
    *,
    organization_id: str,
    multi_city_management: dict[str, Any],
    business_pricing: dict[str, Any],
    demand_forecast: dict[str, Any],
    fraud_prediction: dict[str, Any],
) -> dict[str, Any]:
    incentives = business_pricing.get("incentives", {})
    base_take_rate = _safe_float(incentives.get("commercial_take_rate"), 0.2)
    city_incentives = []
    for city in multi_city_management["city_topology"]:
        if city["demand_index"] >= 60 and city["supply_gap"] > 0:
            bonus = "driver_bonus_20%"
            focus = "supply_gap"
        elif city["demand_index"] >= 35:
            bonus = "availability_bonus_5%"
            focus = "availability"
        else:
            bonus = "network_balance_3%"
            focus = "balance"
        if fraud_prediction["risk_band"] in {"high", "critical"}:
            bonus = "review_only"
        city_incentives.append(
            {
                "city": city["city"],
                "country_code": city["country_code"],
                "currency": city["currency"],
                "bonus": bonus,
                "focus": focus,
                "driver_message": (
                    "Increase driver supply in this market."
                    if focus == "supply_gap"
                    else "Maintain active coverage in this market."
                    if focus == "availability"
                    else "Keep the market balanced."
                ),
                "rider_message": (
                    "Rides remain deterministic while the market stabilizes."
                    if fraud_prediction["risk_band"] in {"high", "critical"}
                    else "Pricing and incentives are within bounded guardrails."
                ),
            }
        )
    return {
        "view": "novaride_phase12_driver_incentives_optimization",
        "commercial_take_rate": round(base_take_rate, 4),
        "incentive_focus": Counter(item["focus"] for item in city_incentives).most_common(1)[0][0] if city_incentives else "balance",
        "city_incentives": city_incentives,
        "driver_message": incentives.get("driver_message", "Global incentives remain bounded and review-ready."),
        "rider_message": incentives.get("rider_message", "Prices remain deterministic and transparent."),
        "demand_snapshot": demand_forecast.get("prediction", {}),
        "optimization_ready": bool(city_incentives),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_auto_decision_engine_projection(
    *,
    organization_id: str,
    phase11: dict[str, Any],
    multi_city_management: dict[str, Any],
    fraud_prediction: dict[str, Any],
    driver_incentives: dict[str, Any],
) -> dict[str, Any]:
    multi_city = multi_city_management
    phase11_ready = bool(phase11["ready"])
    fraud_band = str(fraud_prediction["risk_band"]).lower()
    ready_to_scale = bool(
        phase11_ready
        and multi_city["multi_city_ready"]
        and fraud_band in {"low", "watch"}
        and multi_city["global_coverage_score"] >= 60
    )
    if ready_to_scale and multi_city["mode"] == "global_zero_operator":
        decision_lane = "scale"
        control_signal = "expand_city_orchestration"
    elif ready_to_scale:
        decision_lane = "review"
        control_signal = "rebalance_city_supply"
    else:
        decision_lane = "hold"
        control_signal = "maintain_supervised_operation"
    recommended_actions = [
        "Expand to the strongest city cluster" if decision_lane == "scale" else "Keep city orchestration supervised",
        "Apply regional incentives only within bounded thresholds",
        "Keep fraud prediction and compliance in the review loop",
    ]
    thresholds = {
        "min_active_cities": 2,
        "min_global_coverage": 60,
        "max_predicted_risk_score": 50,
        "max_fraud_band": "watch",
    }
    return {
        "view": "novaride_phase12_auto_decision_engine",
        "decision_lane": decision_lane,
        "control_signal": control_signal,
        "safe_to_autorun": ready_to_scale,
        "confidence": round(
            _clamp((multi_city["global_coverage_score"] + multi_city["global_trust_score"]) / 200.0, minimum=0.0, maximum=1.0),
            2,
        ),
        "decision_summary": (
            "Global zero-operator expansion is safe"
            if decision_lane == "scale"
            else "Bounded review is required before global expansion"
            if decision_lane == "review"
            else "Hold global automation and remain supervised"
        ),
        "recommended_actions": recommended_actions,
        "thresholds": thresholds,
        "phase11_ready": phase11_ready,
        "multi_city_ready": bool(multi_city["multi_city_ready"]),
        "fraud_band": fraud_band,
        "driver_incentive_focus": driver_incentives.get("incentive_focus", "balance"),
        "projection_only": True,
        "read_only": True,
    }


def _phase12_global_learning_projection(
    *,
    organization_id: str,
    multi_city_management: dict[str, Any],
    meta_learning: dict[str, Any],
    digital_twin: dict[str, Any],
    outcome_learning: dict[str, Any],
) -> dict[str, Any]:
    learning = dict(outcome_learning.get("learning", {}))
    cycle = list(learning.get("cycle", []))
    band = learning.get("band", "hold")
    recommendation = (
        "Keep the global learning loop active and learn from the strongest city"
        if multi_city_management["multi_city_ready"]
        else "Hold global learning until additional cities come online"
    )
    return {
        "view": "novaride_phase12_global_learning",
        "band": band,
        "cycle": cycle,
        "recommendations": list(learning.get("recommendations", [])),
        "recalibration_notes": list(learning.get("recalibration_notes", [])),
        "watch_items": list(learning.get("watch_items", [])),
        "outcome_band": outcome_learning.get("current", {}).get("outcome_band", "guarded"),
        "outcome_score": int(outcome_learning.get("current", {}).get("outcome_score", 0) or 0),
        "digital_twin_mode": digital_twin.get("mode", "shadow_sync"),
        "meta_learning_mode": meta_learning.get("mode", "design_hold"),
        "recommendation": recommendation,
        "projection_only": True,
        "read_only": True,
    }


def build_phase12_global_scale_workspace_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_phase12_global_scale",
) -> dict[str, Any]:
    phase11 = build_phase11_compliance_workspace_projection(organization_id=organization_id, limit=limit)
    autonomy = _autonomy_projection(organization_id=organization_id, limit=limit)
    city_automation = _city_automation_projection(organization_id=organization_id, limit=limit)
    multi_city = _multi_city_projection(organization_id=organization_id, limit=limit)
    digital_twin = _digital_twin_projection(organization_id=organization_id, limit=limit)
    meta_learning = _meta_learning_projection(organization_id=organization_id, limit=limit)
    demand_forecast = _demand_projection(organization_id=organization_id, limit=limit)
    business_pricing = _business_pricing_projection(organization_id=organization_id, limit=limit)
    city_profit = _city_profit_projection(organization_id=organization_id, limit=limit)
    outcome_learning = _outcome_learning_projection(organization_id=organization_id, limit=limit)

    multi_city_management = _phase12_multi_city_management_projection(
        organization_id=organization_id,
        phase11=phase11,
        autonomy=autonomy,
        city_automation=city_automation,
        multi_city=multi_city,
        digital_twin=digital_twin,
        demand_forecast=demand_forecast,
        limit=limit,
    )
    geo_fencing = _phase12_geo_fencing_projection(
        organization_id=organization_id,
        multi_city_management=multi_city_management,
        limit=limit,
    )
    currency_support = _phase12_currency_support_projection(
        multi_city_management=multi_city_management,
        business_pricing=business_pricing,
    )
    localization = _phase12_localization_projection(multi_city_management=multi_city_management)
    region_pricing = _phase12_region_pricing_projection(
        multi_city_management=multi_city_management,
        business_pricing=business_pricing,
    )
    distributed_infrastructure = _phase12_distributed_infrastructure_projection(
        multi_city_management=multi_city_management,
    )
    fraud_prediction = _phase12_fraud_prediction_projection(
        organization_id=organization_id,
        phase11=phase11,
        multi_city_management=multi_city_management,
        limit=limit,
    )
    driver_incentives = _phase12_driver_incentives_projection(
        organization_id=organization_id,
        multi_city_management=multi_city_management,
        business_pricing=business_pricing,
        demand_forecast=demand_forecast,
        fraud_prediction=fraud_prediction,
    )
    auto_decision_engine = _phase12_auto_decision_engine_projection(
        organization_id=organization_id,
        phase11=phase11,
        multi_city_management=multi_city_management,
        fraud_prediction=fraud_prediction,
        driver_incentives=driver_incentives,
    )
    global_learning = _phase12_global_learning_projection(
        organization_id=organization_id,
        multi_city_management=multi_city_management,
        meta_learning=meta_learning,
        digital_twin=digital_twin,
        outcome_learning=outcome_learning,
    )

    summary = {
        "multi_city_ready": bool(multi_city_management["multi_city_ready"]),
        "geo_fencing_ready": bool(geo_fencing["geo_fence_ready"]),
        "currency_support_ready": bool(currency_support["currency_support_ready"]),
        "localization_ready": bool(localization["localization_ready"]),
        "region_pricing_ready": bool(region_pricing["region_pricing_ready"]),
        "distributed_infrastructure_ready": bool(distributed_infrastructure["distributed_ready"]),
        "auto_decision_engine_ready": bool(auto_decision_engine["safe_to_autorun"] or auto_decision_engine["decision_lane"] in {"review", "scale"}),
        "fraud_prediction_ready": bool(fraud_prediction["prediction_ready"]),
        "driver_incentives_ready": bool(driver_incentives["optimization_ready"]),
        "global_learning_ready": True,
        "phase11_ready": bool(phase11["ready"]),
        "tenant_isolation_preserved": True,
    }
    ready = all(summary.values())
    global_scale_score = int(
        round(
            _clamp(
                (multi_city_management["global_coverage_score"] * 0.32)
                + (multi_city_management["global_trust_score"] * 0.28)
                + (100 - fraud_prediction["predicted_risk_score"]) * 0.18
                + (80 if localization["localization_ready"] else 0) * 0.1
                + (80 if currency_support["currency_support_ready"] else 0) * 0.1,
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    if global_scale_score >= 85:
        readiness_band = "global_ready"
    elif global_scale_score >= 70:
        readiness_band = "global_review_ready"
    elif global_scale_score >= 50:
        readiness_band = "global_watch"
    else:
        readiness_band = "global_held"

    return {
        "view": "novaride_phase12_global_scale_workspace",
        "phase": "12",
        "platform": "NovaRide Phase 12",
        "organization_id": organization_id,
        "source": source or "afriride_phase12_global_scale",
        "phase11": {
            "ready": bool(phase11["ready"]),
            "summary": phase11["summary"],
            "regulatory_readiness": phase11["regulatory_readiness"],
        },
        "autonomy": autonomy,
        "city_automation": city_automation,
        "multi_city_management": multi_city_management,
        "geo_fencing": geo_fencing,
        "currency_support": currency_support,
        "localization": localization,
        "region_pricing": region_pricing,
        "distributed_infrastructure": distributed_infrastructure,
        "auto_decision_engine": auto_decision_engine,
        "fraud_prediction": fraud_prediction,
        "driver_incentives": driver_incentives,
        "digital_twin": digital_twin,
        "meta_learning": meta_learning,
        "demand_forecast": demand_forecast,
        "business_pricing": business_pricing,
        "city_profit_optimization": city_profit,
        "global_learning": global_learning,
        "summary": summary,
        "readiness_band": readiness_band,
        "global_scale_score": global_scale_score,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
    }


def build_phase12_contract_projection() -> dict[str, Any]:
    return {
        "view": "novaride_phase12_global_scale_contract",
        "status": "controlled_global_scaling_ready",
        "role": "OPERATOR",
        "purpose": "Global scaling layer for multi-city management, geo-fencing, localization, currency support, region pricing, and bounded AI scaling.",
        "modules": [dict(module) for module in NOVARIDE_PHASE12_MODULES],
        "navigation": list(NOVARIDE_PHASE12_NAVIGATION),
        "rbac": {
            "role": "OPERATOR",
            "allowed": list(NOVARIDE_PHASE12_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_PHASE12_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "auto_decision_engine": "projection_only",
            "fraud_prediction": "projection_only",
            "driver_incentives": "projection_only",
            "pricing_authority": "backend_controlled",
            "geo_fencing_authority": "backend_controlled",
            "distributed_infrastructure": "platform_controlled",
            "analytics": "projection_only",
        },
        "api_alignment": {
            "implemented": (
                "/v1/novaride/phase12/status",
                "/v1/novaride/phase12/global-scale-workspace",
                "/v1/novaride/phase12/multi-city-management",
                "/v1/novaride/phase12/geo-fencing",
                "/v1/novaride/phase12/currency-support",
                "/v1/novaride/phase12/localization",
                "/v1/novaride/phase12/region-pricing",
                "/v1/novaride/phase12/distributed-infrastructure",
                "/v1/novaride/phase12/auto-decision-engine",
                "/v1/novaride/phase12/fraud-prediction",
                "/v1/novaride/phase12/driver-incentives",
            ),
            "contract": "/v1/novaride/phase12/global-scale-contract",
        },
        "ecosystem_integrations": {
            "multi_city_orchestration": "city_supply_balancing",
            "digital_twin": "global_state_projection",
            "meta_learning": "proposal_only_redesign_loop",
            "business_pricing": "bounded_region_pricing",
            "city_profit_optimization": "global_margin_projection",
            "phase11_compliance": "regulatory_gate",
            "driver_incentives": "bounded_driver_bonus_projection",
        },
        "advanced_next_phase": (
            "multi_market_automation",
            "adaptive_regional_rollouts",
            "cross_city_capacity_planning",
            "localized_market_expansion",
            "global_execution_guardrails",
        ),
    }


def build_phase12_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workspace = build_phase12_global_scale_workspace_projection(organization_id=org_id, limit=limit)
    summary = workspace["summary"]
    readiness = dict(summary)
    readiness["subscription_active"] = bool(_store().latest_active_subscription(organization_id=org_id))
    ready = bool(workspace["ready"])
    return {
        "view": "novaride_phase12_status",
        "phase": "12",
        "platform": "NovaRide Phase 12",
        "organization_id": org_id,
        "phase11": workspace["phase11"],
        "global_scale_workspace": workspace,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase12_multi_city_management_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["multi_city_management"]


def build_phase12_geo_fencing_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["geo_fencing"]


def build_phase12_currency_support_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["currency_support"]


def build_phase12_localization_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["localization"]


def build_phase12_region_pricing_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["region_pricing"]


def build_phase12_distributed_infrastructure_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["distributed_infrastructure"]


def build_phase12_auto_decision_engine_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["auto_decision_engine"]


def build_phase12_fraud_prediction_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["fraud_prediction"]


def build_phase12_driver_incentives_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["driver_incentives"]


def build_phase12_global_learning_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    return build_phase12_global_scale_workspace_projection(organization_id=organization_id, limit=limit)["global_learning"]


__all__ = [
    "PHASE12_TOPIC",
    "build_phase12_auto_decision_engine_projection",
    "build_phase12_contract_projection",
    "build_phase12_currency_support_projection",
    "build_phase12_distributed_infrastructure_projection",
    "build_phase12_driver_incentives_projection",
    "build_phase12_fraud_prediction_projection",
    "build_phase12_geo_fencing_projection",
    "build_phase12_global_learning_projection",
    "build_phase12_global_scale_workspace_projection",
    "build_phase12_localization_projection",
    "build_phase12_multi_city_management_projection",
    "build_phase12_region_pricing_projection",
    "build_phase12_status",
]
